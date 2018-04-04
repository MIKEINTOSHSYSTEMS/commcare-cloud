import jsonobject
import re

from commcare_cloud.environment.constants import constants


class PostgresqlConfig(jsonobject.JsonObject):
    _allow_dynamic_properties = False

    SEPARATE_SYNCLOGS_DB = jsonobject.BooleanProperty(default=True)
    USE_PARTITIONED_DATABASE = jsonobject.BooleanProperty(default=False)
    DEFAULT_POSTGRESQL_HOST = jsonobject.StringProperty(default=None)
    DEFAULT_POSTGRESQL_USER = jsonobject.StringProperty(default="{{ secrets.POSTGRES_USERS.commcare.username }}")
    DEFAULT_POSTGRESQL_PASSWORD = jsonobject.StringProperty(default="{{ secrets.POSTGRES_USERS.commcare.password }}")
    REPORTING_DATABASES = jsonobject.DictProperty(default=lambda: {"ucr": "ucr"})

    postgresql_dbs = jsonobject.ListProperty(lambda: ShardDBOptions, required=True)
    dbs = jsonobject.ObjectProperty(lambda: SmartDBConfig)

    @property
    def all_dbs(self):
        return self.postgresql_dbs + self.generate_postgresql_dbs()

    @classmethod
    def wrap(cls, data):
        self = super(PostgresqlConfig, cls).wrap(data)
        for db in self.all_dbs:
            if not db.user:
                db.user = self.DEFAULT_POSTGRESQL_USER
            if not db.password:
                db.password = self.DEFAULT_POSTGRESQL_PASSWORD
        return self

    def replace_hosts(self, environment):
        if self.DEFAULT_POSTGRESQL_HOST is None:
            self.DEFAULT_POSTGRESQL_HOST = environment.groups['postgresql'][0]
        elif self.DEFAULT_POSTGRESQL_HOST != '127.0.0.1':
            self.DEFAULT_POSTGRESQL_HOST = environment.translate_host(
                self.DEFAULT_POSTGRESQL_HOST, environment.paths.postgresql_yml)

        for db in self.all_dbs:
            if db.host is None:
                db.host = self.DEFAULT_POSTGRESQL_HOST
            elif db.host != '127.0.0.1':
                db.host = environment.translate_host(db.host, environment.paths.postgresql_yml)

    def generate_postgresql_dbs(self):
        return filter(None, self.dbs.custom + [
            self.dbs.main, self.dbs.formplayer, self.dbs.ucr, self.dbs.synclogs])

    def check(self):
        def get_normalized(db_list):
            return sorted([db.to_json() for db in db_list], key=lambda db: db['name'])

        assert (self.SEPARATE_SYNCLOGS_DB if self.dbs.synclogs is not None
                else not self.SEPARATE_SYNCLOGS_DB), \
            'synclogs should be None if and only if SEPARATE_SYNCLOGS_DB is False'
        assert get_normalized(self.generate_postgresql_dbs()) == \
            get_normalized(self.postgresql_dbs), \
            "{} != {}".format(get_normalized(self.generate_postgresql_dbs()),
                              get_normalized(self.postgresql_dbs))


class SmartDBConfig(jsonobject.JsonObject):
    _allow_dynamic_properties = False

    main = jsonobject.ObjectProperty(lambda: MainDBOptions, required=True)
    formplayer = jsonobject.ObjectProperty(lambda: FormplayerDBOptions, required=True)
    ucr = jsonobject.ObjectProperty(lambda: UcrDBOptions, required=True)
    synclogs = jsonobject.ObjectProperty(lambda: SynclogsDBOptions, required=False)

    custom = jsonobject.ListProperty(lambda: ShardDBOptions)


class DBOptions(jsonobject.JsonObject):
    _allow_dynamic_properties = False

    name = jsonobject.StringProperty(required=True)
    host = jsonobject.StringProperty()
    port = jsonobject.IntegerProperty(default=6432)
    user = jsonobject.StringProperty()
    password = jsonobject.StringProperty()
    options = jsonobject.DictProperty(unicode)
    django_alias = jsonobject.StringProperty()
    django_migrate = jsonobject.BooleanProperty(default=True)
    query_stats = jsonobject.BooleanProperty(default=False)
    create = jsonobject.BooleanProperty(default=True)

    @classmethod
    def wrap(cls, data):
        self = super(DBOptions, cls).wrap(data)
        if re.match('^{{\s*commcarehq_main_db_name\s*}}$', self.name):
            self.name = constants.commcarehq_main_db_name
        if re.match('^{{\s*formplayer_db_name\s*}}$', self.name):
            self.name = constants.formplayer_db_name
        return self


class MainDBOptions(DBOptions):
    name = constants.commcarehq_main_db_name
    django_alias = 'default'


class FormplayerDBOptions(DBOptions):
    name = constants.formplayer_db_name
    django_alias = None


class UcrDBOptions(DBOptions):
    name = constants.ucr_db_name
    django_alias = 'ucr'
    django_migrate = False


class SynclogsDBOptions(DBOptions):
    name = constants.synclogs_db_name
    django_alias = 'synclogs'


class ShardDBOptions(DBOptions):
    shards = jsonobject.ListProperty(int, exclude_if_none=True)  # [start, end] pair
