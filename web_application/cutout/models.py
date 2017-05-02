from django.db import models


class Cutout(models.Model):
    # ---- POSITION ----
    objId = models.IntegerField(blank=True)
    ra = models.FloatField(blank=True)
    dec = models.FloatField(blank=True)
    radius = models.FloatField(blank=True)

    # ---- WAVELENGTH ----
    greyscale = models.BooleanField(default=True)

    CHANDRA = 'CH'
    GALEX = 'GA'
    HST = 'HST'
    SDSS = 'SDSS'
    VIKING = 'VIKING'

    AVAILABLE_BANDS = (
        (CHANDRA, 'Chandra'),
        (GALEX, 'GALEX'),
        (HST, 'HST'),
        (SDSS, 'SDSS'),
        (VIKING, 'VIKING'),
    )

    bands = models.CharField(
        max_length=len(AVAILABLE_BANDS),
        choices=AVAILABLE_BANDS,
        default=SDSS,
    )

    rgb = models.BooleanField(default=False)
    rgbRed = models.CharField(max_length=1, choices=AVAILABLE_BANDS, default=SDSS)
    rgbGreen = models.CharField(max_length=1, choices=AVAILABLE_BANDS, default=VIKING)
    rgbBlue = models.CharField(max_length=1, choices=AVAILABLE_BANDS, default=SDSS)

    # ---- CONTOUR DATA ----
    contourBand = models.CharField(
        max_length=1,
        choices=AVAILABLE_BANDS,
        default=SDSS,
    )
    contourLevels = models.FloatField(blank=True)

    # ---- IMAGE SCALING ----
    INPUT_SCALING = (
        ("LOG", 'log'),
        ("LINEAR", 'linear'),
        ("ATAN", 'atan'),
        ("ASINH", 'asinh'),
    )
    inputScaling  = models.CharField(
        max_length=1,
        choices=AVAILABLE_BANDS,
        default=SDSS,
    )

    stretchScale = models.FloatField(default=1)

    # ---- PLOT OPTIONS ----
    axisStyle = models.CharField(
        max_length=1,
        choices=(('BASIC', 'Basic'), ('INSET', 'Inset'), ("NONE", 'None')),
        default="BASIC",
    )

    scaleBar = models.BooleanField(default=False)
    scaleBarz = models.FloatField(blank=True)
    imageColor = models.CharField(max_length=1, choices=(("HEAT", 'Heat'), ("GREY", 'grey')))
    invertColor = models.BooleanField(default=False)

    # ---- ADDITIONAL OPTIONS ----
    overplotGAMAsources = models.BooleanField(default=False)
    overplotGAMAapertures = models.BooleanField(default=False)
    overplotIOTAapertures = models.BooleanField(default=False)

    overplotSAMIsources = models.BooleanField(default=False)