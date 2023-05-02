from django.contrib.auth import get_user_model

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

class NestedUserDefault:
    '''
    Returns the parent user in the URI. ONLY FOR 1 NESTED LEVEL!

    This is useful when you want resources under a user, but want admins to
    be able to create/edit resources for that user. CurrentUserDefault uses
    the logged-in user, so having something like a creator field on the
    resource would default to the admin rather than the user upon writing.
    
    NOTE: This only works is user is the only parent!
        users/<pk>/groups --> we would use pk to get the User
        
        If we had instead:
        users/<pk>/groups/<pk> --> this class may not work correctly
    '''
    requires_context = True

    def __call__(self, serializer_field):
        kwargs = serializer_field.context.get('view', None)
        if kwargs is None:
            raise ValueError("Must contain the view in the context dict")
        # Get first element in the kwargs dict. None if dict is empty.
        user_id = next(iter(kwargs.values()), None)
        if user_id is None:
            raise ValueError("There is no parent user resource in the URI")
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            user = None
        return user

    def __repr__(self):
        return '%s()' % self.__class__.__name__
