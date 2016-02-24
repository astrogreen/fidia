from django.db import models
from jsonfield import JSONField
from datetime import datetime
from django.utils.text import slugify

ASTRO_TYPE = [('galaxy', 'galaxy'), ('star', 'star'), ('group', 'group')]
DATA_RELEASE = [('dr1', 'dr1'), ('dr2', 'dr2')]
PUBLIC_TEAM = [('public', 'public'), ('team', 'team')]
SURVEYS_NAMES = [('gama', 'gama'), ('sami', 'sami')]
CAT_GROUPS = [('GroupFinding', 'GroupFinding'), ('InputCat', 'InputCat')]
PRODUCTS = [('img', 'img'), ('cat', 'cat'), ('spectra','spectra')]


class Query(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    title = models.CharField(max_length=100, blank=True, default="")
    SQL = models.TextField()
    queryResults = JSONField(default="")
    owner = models.ForeignKey('auth.User', related_name='query')

    class Meta:
        ordering = ('created',)



# NEW DATA MODEL - - -

class Survey(models.Model):
    title = models.CharField(choices=SURVEYS_NAMES, max_length=100, unique=True)

    #define string representation (else defaults to 'Survey Object')
    def __str__(self):     # or def __unicode__(self) in Python 2
        return self.title


class SurveyMetaData(models.Model):
    info=models.CharField(max_length=100)
    survey = models.ForeignKey(
        'Survey',
        on_delete=models.CASCADE,
        related_name='surveymetadata'
    )


class ReleaseType(models.Model):
    survey = models.ForeignKey(
        'Survey',
        on_delete=models.CASCADE,
        related_name='releasetype'
    )
    releaseTeam = models.CharField(choices=PUBLIC_TEAM, max_length=100)
    dataRelease = models.CharField(choices=DATA_RELEASE, max_length=100)
    slugField = models.SlugField(max_length=200, unique=True, null=True)

    def save(self, *args, **kwargs):
        # just check if name or location.name has changed
        self.slugField = '-'.join((slugify(self.survey.title), slugify(self.releaseTeam), slugify(self.dataRelease)))
        super(ReleaseType, self).save(*args, **kwargs)

    def __str__(self):     # or def __unicode__(self) in Python 2
        return '%s' % (self.slugField)



class CatalogueGroup(models.Model):
    group = models.CharField(choices=CAT_GROUPS, max_length=100, unique=True)
    slugField = models.SlugField(max_length=200, unique=True, null=True)

    def save(self, *args, **kwargs):
        # just check if name or location.name has changed
        self.slugField = (self.group)
        super(CatalogueGroup, self).save(*args, **kwargs)

    def __str__(self):     # or def __unicode__(self) in Python 2
        return '%s' % (self.group)


class Catalogue(models.Model):
    release = models.ManyToManyField(
        'ReleaseType',
        related_name='catalogue'
    )
    title = models.CharField(max_length=100)
    content = JSONField(default="table of content")
    meta = JSONField(default="metadata")
    catalogueGroup = models.ForeignKey(
        'CatalogueGroup',
        on_delete=models.CASCADE,
        related_name='catalogue'
    )
    version = models.DecimalField(decimal_places=2, max_digits=4)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    slugField = models.SlugField(max_length=200, unique=True, null=True)

    def save(self, *args, **kwargs):
        # just check if name or location.name has changed
        self.slugField = '-v'.join(((self.title), slugify(self.version)))
        super(Catalogue, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.slugField)


class Image(models.Model):
    release = models.ManyToManyField(
        'ReleaseType',
        related_name='image'
    )
    title = models.CharField(max_length=100,null=True, blank=True)
    content = models.ImageField(blank=True, upload_to='uploads/%Y/%m/%d/', null=True)
    meta = JSONField(default="",null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    version = models.DecimalField(decimal_places=2, max_digits=4, default=0)
    slugField = models.SlugField(max_length=200, unique=True, null=True)

    def save(self, *args, **kwargs):
        #TODO - need to save and then update instance to use m2m field
        # self.slugField = '-v'.join((((self.release.slugField),(self.title), slugify(self.version))))
        self.slugField = '-v'.join((((self.title), slugify(self.version))))
        super(Image, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.slugField)



class Spectrum(models.Model):
    release = models.ManyToManyField(
        'ReleaseType',
        related_name='spectrum'
    )
    title = models.CharField(max_length=100,null=True, blank=True)
    content = models.ImageField(blank=True, upload_to='uploads/%Y/%m/%d/', null=True)
    meta = JSONField(default="metadata",null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    version = models.DecimalField(decimal_places=2, max_digits=4, default=0)
    slugField = models.SlugField(max_length=200, unique=True, null=True)

    def save(self, *args, **kwargs):
        # just check if name or location.name has changed
        self.slugField = '-v'.join(((self.release.slugField),(self.title), slugify(self.version)))
        super(Spectrum, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.slugField)


class AstroObject(models.Model):
    type=models.CharField(choices=ASTRO_TYPE,max_length=100)

    def number(self):
        num = AstroObject.objects.count()
        if num == None:
            return 1
        else:
            return num + 1

    ASVOID = models.IntegerField(unique=True, default=number)
    catalogue = models.ManyToManyField(
        'Catalogue',
        related_name='astroobject'
    )
    image = models.ManyToManyField(
        'Image',
        related_name='astroobject'
    )
    spectrum = models.ManyToManyField(
        'Spectrum',
        related_name='astroobject'
    )




#END NEW DATA MODEL - - -



class GAMAPublic(models.Model):
    ASVOID = models.CharField(max_length=100)
    InputCatA = JSONField(default="", blank=True)
    TilingCat = JSONField(default="", blank=True)
    SpecAll = JSONField(default="", blank=True)
    SersicCat = JSONField(default = "", blank=True)
    Spectrum = models.ImageField(blank=True, upload_to='uploads/%Y/%m/%d/', null=True)




# TEST NEW ASTROOBJECT ON MODEL
# def manufacture_model_for_archive(archive):

class TestFidiaSchema(models.Model):
    redshift = models.CharField(max_length=100, blank=True)


    # return TestFidiaSchema