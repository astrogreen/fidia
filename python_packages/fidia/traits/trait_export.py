

#  __       ___          ___      __   __   __  ___                        __
# |  \  /\   |   /\     |__  \_/ |__) /  \ |__)  |      |\/| | \_/ | |\ | /__`
# |__/ /~~\  |  /~~\    |___ / \ |    \__/ |  \  |      |  | | / \ | | \| .__/
#
# Mixin classes to handle various special kinds of data export.
#
# These are provided as mix-in classes because they may not be appropriate to any/all Traits.


class FITSExportMixin:
    """A Trait Mixin class which adds FITS Export to the export options for a Trait."""

    def as_fits(self, file):
        """FITS Exporter

        :param  file
            file is either a file-like object, or a string containing the path
            of a file to be created. In the case of the string, the file will be
            created, written to, and closed.

        :returns None

        """

        assert isinstance(self, Trait)
        if not hasattr(self, 'value'):
            raise ExportException("Trait '%s' cannot be exported as FITS" % str(self))

        # Create a function holder which can be set to close the file if it is opened here
        file_cleanup = lambda: None
        if isinstance(file, str):
            file = open(file, 'wb')
            # Store pointer to close function to be called at the end of the this function.
            file_cleanup = file.close

        hdulist = fits.HDUList()

        # Check if a WCS is present as a SmartTrait:
        try:
            wcs_smarttrait = self['wcs']
        except KeyError:
            log.debug("No WCS information available for export to FITS in Trait %s", self)
            def add_wcs(hdu):
                # type: (fits.PrimaryHDU) -> fits.PrimaryHDU
                return hdu
        else:
            def add_wcs(hdu):
                # type: (fits.PrimaryHDU) -> fits.PrimaryHDU
                log.debug("Adding WCS information to extension %s", hdu)
                hdu.header.extend(wcs_smarttrait.to_header())
                return hdu

        # Value should/will always be the first item in the FITS File (unless it cannot
        # be put in a PrimaryHDU, e.g. because it is not "image-like")

        if type(self).value.type.startswith("float.array") or type(self).value.type.startswith("int.array"):
            primary_hdu = fits.PrimaryHDU(self.value())
            # Add unit information to header if present
            if hasattr(self, 'unit'):
                if hasattr(self.unit, 'value'):
                    primary_hdu.header['BUNIT'] = str(self.unit.value) + self.unit.unit.to_string()
                else:
                    primary_hdu.header['BUNIT'] = self.unit.to_string()

        elif type(self).value.type in ("float", "int"):
            primary_hdu = fits.PrimaryHDU([self.value()])
        else:
            log.error("Attempted to export trait with value type '%s'", type(self).value.type)
            file_cleanup()
            # @TODO: Delete the file (as it is invalid anyway)?
            raise ExportException("Trait '%s' cannot be exported as FITS" % str(self))

        # Add the newly created PrimaryHDU to the FITS file.
        add_wcs(primary_hdu)
        hdulist.append(primary_hdu)

        # Add documentation information to PrimaryHDU
        primary_hdu.header['OBJECT'] = self.object_id
        primary_hdu.header['DATAPROD'] = (self.trait_name, "Data Central product ID")
        # primary_hdu.header['DATANAME'] = (self.get_pretty_name().encode('ascii', errors='ignore'), "Data Product Name")
        # primary_hdu.header['SHRTDESC'] = (self.get_description().encode('ascii', errors='ignore'))
        primary_hdu.header['BRANCH'] = (self.branch, "Data Central Branch ID")
        primary_hdu.header['VER'] = (self.version, "Data Central Version ID")
        primary_hdu.header['EXTNAME'] = self.get_short_name()

        # Attach all "meta-data" Traits to Header of Primary HDU
        from . import meta_data_traits
        for sub_trait in self.get_all_subtraits():
            log.debug("Searching for metadata in subtrait '%s'...", sub_trait)
            if not isinstance(sub_trait, meta_data_traits.MetadataTrait):
                continue
            log.debug("Adding metadata trait '%s'", sub_trait)
            # MetadataTrait will have a bunch of Trait Properties which should
            # be appended individually, so we iterate over each Trait's
            # TraitProperties
            for trait_property in sub_trait.trait_properties(['float', 'int', 'string']):
                try:
                    keyword_name = trait_property.get_short_name()
                    keyword_value = trait_property.value
                    keyword_comment = trait_property.get_description()
                    log.debug("Adding metadata TraitProperty '%s' to header", keyword_name)
                    primary_hdu.header[keyword_name] = (
                        keyword_value,
                        keyword_comment)
                    del keyword_name, keyword_value, keyword_comment
                except DataNotAvailable:
                    log.warning(
                        "Trait Property '%s' not added to FITS file because it's data is not available.",
                        trait_property)

        # Attach all simple value Traits to header of Primary HDU:
        # for trait in self.get_sub_trait(Measurement):
        #     primary_hdu.header[trait.short_name] = (trait.value, trait.short_comment)
        #     primary_hdu.header[trait.short_name + "_ERR"] = (trait.value, trait.short_comment)

        # Create extensions for additional array-like values
        for trait_property in self.trait_properties(
                RegexpGroup(re.compile(r"float\.array\.\d+"),
                            re.compile(r"int\.array\.\d+"))):
            if trait_property.name == 'value':
                continue
            try:
                extension = fits.ImageHDU(trait_property.value)
                extension.name = trait_property.get_short_name()
                # Add the same WCS if appropriate
                add_wcs(extension)
                extension.header['EXTID'] = (trait_property.name, "Data Product Extension ID")
                # extension.header['EXTNAME'] = (trait_property.get_pretty_name().encode('ascii', errors='ignore'), "Data Product Extension Name")
                # extension.header['SHRTDESC'] = (trait_property.get_description().encode('ascii', errors='ignore'))

                hdulist.append(extension)
                del extension
            except DataNotAvailable:
                log.warning(
                    "Trait Property '%s' not added to FITS file because it's data is not available.",
                    trait_property)

        # Add single-numeric-value TraitProperties to the primary header:
        for trait_property in self.trait_properties(['float', 'int']):
            try:
                keyword_name = trait_property.get_short_name()
                keyword_value = trait_property.value
                keyword_comment = trait_property.get_description()
                log.debug("Adding numeric TraitProperty '%s' to header", keyword_name)
                primary_hdu.header[keyword_name] = (
                    keyword_value,
                    keyword_comment)
                del keyword_name, keyword_comment, keyword_value
            except DataNotAvailable:
                log.warning(
                    "Trait Property '%s' not added to FITS file because it's data is not available.",
                    trait_property)

        # Add string value TraitProperties to the primary header
        for trait_property in self.trait_properties(['string']):

            # Skip "HISTORY" which is handled below
            if trait_property.name == "history":
                continue

            try:
                keyword_name = trait_property.get_short_name()
                keyword_value = trait_property.value
                keyword_comment = trait_property.get_description()
                if len(keyword_value) >= 80:
                    # This value won't fit, so skip it.
                    # @TODO: Issue a warning?
                    log.warning("TraitProperty '%s' skipped because it is to long to fit in header", trait_property)
                    continue
                log.debug("Adding string TraitProperty '%s' to header", keyword_name)
                primary_hdu.header[keyword_name] = (
                    keyword_value,
                    keyword_comment)
                del keyword_name, keyword_comment, keyword_value
            except DataNotAvailable:
                log.warning(
                    "Trait Property '%s' not added to FITS file because it's data is not available.",
                    trait_property)

        # Add history information
        if hasattr(self, 'history'):
            for line in self.history.value.splitlines():
                primary_hdu.header['HISTORY'] = line

        # Create extensions for sub-traits:
        for trait in self.get_all_subtraits():
            if hasattr(trait, 'as_fits_extension'):
                extension = trait.as_fits_extension()
                hdulist.append(extension)
                continue
            for trait_property in trait.trait_properties(
                RegexpGroup(re.compile(r"float\.array\.\d+"),
                            re.compile(r"int\.array\.\d+"))):
                extension = fits.ImageHDU(trait_property.value)

                # Set the name of the extension for this trait property. As this
                # is a sub-trait, we use the sub-trait name, and if the trait
                # property is not 'value', we append '_name' to the extension
                # name.
                if trait_property.name == 'value':
                    extension.name = str(trait.get_short_name())
                else:
                    extension.name = str(trait.get_short_name()) + "_" + str(trait_property.get_short_name())

                # Store other vital information about the origin of this data in the header.
                extension.header['SUBTRAIT'] = (trait.trait_name, "Data Central Sub-trait ID")
                # extension.header['ST_NAME'] = (trait.get_pretty_name().encode('ascii', errors='ignore'), "Sub-trait Name")
                # extension.header['ST_DESC'] = (trait.get_description().encode('ascii', errors='ignore'))
                extension.header['EXTID'] = (trait_property.name, "Data Central Sub-trait Data ID")
                # extension.header['EXTNAME'] = (trait_property.get_pretty_name().encode('ascii', errors='ignore'), "Sub-trait Data Name")
                # extension.header['EXTDESC'] = (trait_property.get_description().encode('ascii', errors='ignore'))

                # Add unit information to header if present
                if hasattr(trait_property, 'unit') \
                        or (hasattr(trait, 'unit') and trait_property.name == 'value'):
                    if hasattr(trait_property, 'unit'):
                        unit = trait_property.unit
                    else:
                        unit = trait.unit
                    if hasattr(unit, 'value'):
                        extension.header['BUNIT'] = str(unit.value) + unit.unit.to_string()
                    else:
                        extension.header['BUNIT'] = unit.to_string()

                # Add single-numeric-value TraitProperties to the primary header:
                for trait_property in trait.trait_properties(['float', 'int']):
                    try:
                        keyword_name = trait_property.get_short_name()
                        keyword_value = trait_property.value
                        keyword_comment = trait_property.get_description()
                        log.debug("Adding numeric TraitProperty '%s' to header", keyword_name)
                        extension.header[keyword_name] = (
                            keyword_value,
                            keyword_comment)
                        del keyword_name, keyword_comment, keyword_value
                    except DataNotAvailable:
                        log.warning(
                            "Trait Property '%s' not added to FITS file because it's data is not available.",
                            trait_property)

                # Add string value TraitProperties to the primary header
                for trait_property in trait.trait_properties(['string']):

                    # Skip "HISTORY" which is handled below
                    if trait_property.name == "history":
                        continue

                    try:
                        keyword_name = trait_property.get_short_name()
                        keyword_value = trait_property.value
                        keyword_comment = trait_property.get_description()
                        if len(keyword_value) >= 80:
                            # This value won't fit, so skip it.
                            # @TODO: Issue a warning?
                            log.warning("TraitProperty '%s' skipped because it is to long to fit in header",
                                        trait_property)
                            continue
                        log.debug("Adding string TraitProperty '%s' to header", keyword_name)
                        extension.header[keyword_name] = (
                            keyword_value,
                            keyword_comment)
                        del keyword_name, keyword_comment, keyword_value
                    except DataNotAvailable:
                        log.warning(
                            "Trait Property '%s' not added to FITS file because it's data is not available.",
                            trait_property)


                hdulist.append(extension)

        # Create extensions for additional record-array-like values (e.g. tabular values)
        # for trait_property in self.trait_property_values('catalog'):
        #     extension = fits.BinTableHDU(trait_property)
        #     hdulist.append(extension)

        hdulist.verify('exception')
        hdulist.writeto(file)

        # If necessary, close the open file handle.
        file_cleanup()
