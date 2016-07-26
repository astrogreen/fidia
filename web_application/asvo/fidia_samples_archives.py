from django.conf import settings

from fidia.archive import sami


# sami_team_archive = sami.SAMITeamArchive(
#     settings.SAMI_TEAM_DATABASE,
#     settings.SAMI_TEAM_DATABASE_CATALOG)

sami_dr1_archive = sami.SAMIDR1PublicArchive(
    settings.SAMI_DR1_DATABASE,
   settings.SAMI_DR1_DATABASE_CATALOG)

sami_dr1_sample = sami_dr1_archive.get_full_sample()

