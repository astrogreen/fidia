import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
print('--- loading ldap ---')

# AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_X_TLS_CACERTDIR, '/etc/ssl/certs'}

# ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, '/etc/ssl/certs')
# ldap.set_option('TLS_CACERT', '/Users/lmannering/Documents/certs')

# ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

# Baseline configuration.
# AUTH_LDAP_SERVER_URI = "ldaps://aaopca.asvo.aao.gov.au:636"
AUTH_LDAP_SERVER_URI = "ldap://aaopca.asvo.aao.gov.au"

# AUTH_LDAP_BIND_DN = "ASVO\adc_connect"
# AUTH_LDAP_BIND_DN = "cn=adc_connect,cn=Users,dc=ASVO,dc=AAO,dc=gov,dc=au"
AUTH_LDAP_BIND_DN = "adc_connect@ASVO.AAO.GOV.AU"
AUTH_LDAP_BIND_PASSWORD = "2BL0gged1n"
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=Standard,ou=Accounts,dc=asvo,dc=aao,dc=gov,dc=au",
                                   ldap.SCOPE_SUBTREE, "(&(objectClass=*)(sAMAccountName=%(user)s))")

# Populate the Django user from the LDAP directory.
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# enable TLS via start_tls_s() on default LDAP port 389
AUTH_LDAP_START_TLS = True

# This is the default, but I like to be explicit.
AUTH_LDAP_ALWAYS_UPDATE_USER = True

AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_DEBUG_LEVEL: 0,
    ldap.OPT_REFERRALS: 0,
}

# Keep ModelBackend around for per-user permissions and maybe a local
# superuser.
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
