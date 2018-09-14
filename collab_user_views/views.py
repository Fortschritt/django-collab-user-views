# -*- coding: utf-8 -*-

import json
from django import forms
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import ugettext as _
from collab.shortcuts import get_objects_for_user
from spaces.models import Space
from collab.decorators import manager_required
from actstream.models import Action, model_stream
from actstream.signals import action as actstream_action


def get_accessible_spaces(user):
    """
    returns all spaces the given user has the "access_space" right.
    """
    if not user:
        return []
    obj_list = get_objects_for_user(user, 'access_space',Space)\
                .order_by('-created_at')
    return obj_list

def get_own_spaces(user):
    """
    returns all spaces the given user is a member of.
    """
    if not user:
        return []
    own_spaces = []
    accessible_spacs = get_accessible_spaces(user)
    for space in accessible_spacs:
        group_ids = [space.get_team().id, space.get_members().id, space.get_admins().id]
        if user.groups.filter(id__in = group_ids):
            own_spaces.append(space)
    return own_spaces

def get_created_spaces(user):
    """
    return spaces that have been created by the given user.
    """
    if not user:
        return []
    created_spaces = Space.objects.filter(created_by=user)\
                        .order_by('-created_at')
    return created_spaces

def get_manager_stream():
    """
    Return a list of recent activities of interest for users with
    the manager role.
    """
    # we only want activities where the object is either a user or a space,
    # e.g. user creation/role change/deletion or space creation/role change/deletion
    type_list = [
        ContentType.objects.get_for_model(get_user_model()),
        ContentType.objects.get_for_model(Space)
    ]
    ret = Action.objects.public(action_object_content_type__in=type_list)[:10]
    return ret

def get_user_stream(user):
    """
    Return a list of recent activities of interest for normal users.
    """
    spaces = get_accessible_spaces(user)
    ret = model_stream(Space, target_object_id__in=spaces)[:10]
    return ret

@login_required
def dashboard(request):
    extra_context = {}
    extra_context['accessible_spaces'] = get_accessible_spaces(request.user)
    extra_context['own_spaces'] = get_own_spaces(request.user)
    extra_context['created_spaces'] = get_created_spaces(request.user)
    extra_context['user_stream'] = get_user_stream(request.user)
    if request.user.is_superuser or request.user.collab.is_manager:
        extra_context['manager_stream'] = get_manager_stream()
    return render(request,'collab_user_views/dashboard.html',extra_context) 

@manager_required
def create_space(request):
    """
    Displaying and processing a form for creating new Space instances.
    """
    extra_context = {}
    if request.method == "POST":
        name = None
        try:
            name = request.POST['space_name']
        except KeyError:
            messages.error(request, _("Please set a name for the new Space."))
        if name:
            key = 'space_expires'
            expires = request.POST[key] if key in request.POST.keys() else ''
            expires = expires if len(expires) > 1 else None
            #print(expires)
            datefield = forms.DateTimeField()
            expires = datefield.to_python(expires)
            new_space = Space.objects.create(name=name, 
                            expires=expires, created_by = request.user)
            messages.success(request, _("Space \"%s\" successfully created.") \
                % new_space.name)
            actstream_action.send(
                sender=request.user,
                verb=_("was created"),
                action_object=new_space
            )
            return redirect(new_space.get_absolute_url())
    return render(request, 'collab_user_views/create_space_form.html', 
                        extra_context)


@login_required
def help(request):
    """
    Display end user docs for the platform.
    """
    return render(request, 'collab_user_views/help.html', {})