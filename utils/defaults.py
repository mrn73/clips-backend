
class CurrentUserIDDefault:
    '''
    Alternative version of serializers.CurrentUserDefault that returns
    the ID of the user, rather than the whole user instance.

    Using this allows you to set a default user on a foreign key field by using
    <field_name>_id, freeing up <field_name> to be a different represention for
    serialization.

    EX: 
        owner_id = serializers.HiddenField(default=CurrentUserIDDefault())
        owner = serializers.StringRelatedField() #read_only be default
    This would allow you to submit the owner of an object behind the scenes, but also
    allow the owner to be shown in the serialized output as a string.
    '''
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['request'].user.id

    def __repr__(self):
        return '%s()' % self.__class__.__name__
