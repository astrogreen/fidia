
class TraitProperty:
    pass

class DataLoader:
    def __init__(self, column_id):
        self.colun_id = column_id

    def __get__(self, instance, owner):
        if instance is None:
            print('returning DataLoader')
            return self
        print("__get__ called with instance: %s, and owner: %s" % (instance, owner))


class Trait:

    trait_mapping = dict()

    def __init__(self, object_id, trait_mapping):
        self.trait_mapping = trait_mapping
        self.object_id = object_id
        # for attr in dir(self):
        #     if isinstance(getattr(self, attr), TraitProperty):
        #         if attr in self.trait_mapping:
        #             value = DataLoader(self.trait_mapping[attr], self.object_id)
        #
        #             setattr(self, attr, value)
        #         else:
        #             raise Exception("required property %s not set" % attr)

    def __new__(cls, object_id, trait_mapping):
        class LocalTrait(cls):
            pass
        for attr in dir(cls):
            if isinstance(getattr(cls, attr), TraitProperty):
                if attr in trait_mapping:
                    value = DataLoader(trait_mapping[attr])

                    setattr(LocalTrait, attr, value)
                else:
                    raise Exception("required property %s not set" % attr)
        res = LocalTrait.__new__(LocalTrait, object_id, trait_mapping)
        print('Completing __new__')
        return res

class Image(Trait):

    data = TraitProperty()

i = Image("123", {'data': "col1"})