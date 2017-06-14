import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

print('--- loading ldap ---')

# Baseline configuration.
AUTH_LDAP_SERVER_URI = "ldap://asvo.aao.gov.au"

AUTH_LDAP_BIND_DN = "cn=adbinder,ou=accounts,ou=admin,dc=asvo,dc=aao,dc=gov,dc=au"
AUTH_LDAP_BIND_PASSWORD = "2BL0gged1n"
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=accounts,dc=asvo,dc=aao,dc=gov,dc=au",
                                   ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
# or perhaps:
# AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=users,dc=example,dc=com"

# Set up the basic group parameters.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch("ou=surveys,ou=accounts,dc=asvo,dc=aao,dc=gov,dc=au",
                                    ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)"
                                    )
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")

# Simple group restrictions
AUTH_LDAP_REQUIRE_GROUP = "cn=enabled,ou=django,ou=groups,dc=example,dc=com"
AUTH_LDAP_DENY_GROUP = "cn=disabled,ou=django,ou=groups,dc=example,dc=com"

# Populate the Django user from the LDAP directory.
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# We might need this kind of thing later
# AUTH_LDAP_PROFILE_ATTR_MAP = {
#    "employee_number": "employeeNumber"
# }

# We might need this kind of thing later
# AUTH_LDAP_USER_FLAGS_BY_GROUP = {
#    "is_active": "cn=active,ou=django,ou=groups,dc=example,dc=com",
#    "is_staff": "cn=staff,ou=django,ou=groups,dc=example,dc=com",
#    "is_superuser": "cn=superuser,ou=django,ou=groups,dc=example,dc=com"
# }

# We might need this kind of thing later
# AUTH_LDAP_PROFILE_FLAGS_BY_GROUP = {
#    "is_awesome": "cn=awesome,ou=django,ou=groups,dc=example,dc=com",
# }

# This is the default, but I like to be explicit.
AUTH_LDAP_ALWAYS_UPDATE_USER = True

# Use LDAP group membership to calculate group permissions.
AUTH_LDAP_FIND_GROUP_PERMS = True

# Cache group memberships for an hour to minimize LDAP traffic
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600

# Keep ModelBackend around for per-user permissions and maybe a local
# superuser.
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)