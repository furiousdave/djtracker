from djtracker import models, choices, utils, forms

from django.http import HttpResponseNotFound
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.views.generic import list_detail
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse

def index(request):
    projects = models.Project.objects.filter(active=True)
    viewable_projects = []
    for x in projects:
        can_view, can_edit, can_comment = utils.check_perms(request, x)
        if can_view:
            viewable_projects.append(x.id)

    display_projects = models.Project.objects.filter(id__in=viewable_projects)

    return list_detail.object_list(request,
        queryset=display_projects,
        extra_context={'user': request.user, 'request': request},
        paginate_by=10,
        allow_empty=True,
        template_name="djtracker/index.html",
        template_object_name="project"
    )

def view_category(request, cat_slug):
    category = get_object_or_404(models.Category, slug=cat_slug)
    project_ids = []
    for x in category.project_set.all():
        can_view, can_edit, can_comment = utils.check_perms(request, x)
        if can_view:
            project_ids.append(x.id)

    project_list = models.Project.objects.filter(id__in=project_ids)
    return render_to_response(
        "djtracker/index.html", locals(),
        context_instance=RequestContext(request))

def project_index(request, project_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    open_issues = project.issue_set.filter(status="Open")
    can_view, can_edit, can_comment = utils.check_perms(request, project)
    if can_view is False:
        return HttpResponseNotFound()
    else:
        return list_detail.object_detail(request,
            queryset=models.Project.objects.all(),
            extra_context={'can_comment': can_comment,
                'open_issues': open_issues[:5]},
            slug=project_slug,
            template_name="djtracker/project_index.html",
            template_object_name="project"
        )

def project_all_issues(request, project_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    issues = project.issue_set.all()
    can_view, can_edit, can_comment = utils.check_perms(request, project)
    status_choices = choices.STATUS_OPTIONS_ARRAY
    priority_choices = choices.PRIORITIES_ARRAY
    type_choices = choices.BUG_TYPES_ARRAY
    if 'component' in request.GET:
        if request.GET.get('component'):
            issues = issues.filter(component__slug=request.GET.get('component'))
    if 'version' in request.GET:
        if request.GET.get('version'):
            issues = issues.filter(version__slug=request.GET.get('version'))
    if 'milestone' in request.GET:
        if request.GET.get('milestone'):
            issues = issues.filter(milestone__slug=request.GET.get('milestone'))
    if 'status' in request.GET:
        if request.GET.get('status'):
            issues = issues.filter(status=request.GET.get('status'))
    if 'type' in request.GET:
        if request.GET.get('type'):
            issues = issues.filter(issue_type=request.GET.get('type'))
    if 'priority' in request.GET:
        if request.GET.get('priority'):
            issues = issues.filter(priority=request.GET.get('priority'))

    if can_view is False:
        return HttpResponseNotFound()
    else:
        return render_to_response(
            "djtracker/issue_view_all.html", locals(),
            context_instance=RequestContext(request))

def project_component(request, project_slug, modi_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    modifier = get_object_or_404(models.Component, slug=modi_slug)
    modifier_type = "Component"
    can_view, can_edit, can_comment = utils.check_perms(request, project)
    if can_view is False:
        return HttpResponseNotFound()
    else:
        return render_to_response(
            "djtracker/modifier_view.html", locals(),
            context_instance=RequestContext(request))

def project_milestone(request, project_slug, modi_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    modifier = get_object_or_404(models.Milestone, slug=modi_slug)
    modifier_type = "Milestone"
    can_view, can_edit, can_comment = utils.check_perms(request, project)
    if can_view is False:
        return HttpResponseNotFound()
    else:
        return render_to_response(
            "djtracker/modifier_view.html", locals(),
            context_instance=RequestContext(request))

def project_version(request, project_slug, modi_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    modifier = get_object_or_404(models.Version, slug=modi_slug)
    modifier_type = "Version"
    can_view, can_edit, can_comment = utils.check_perms(request, project)
    if can_view is False:
        return HttpResponseNotFound()
    else:
        return render_to_response(
            "djtracker/modifier_view.html", locals(),
            context_instance=RequestContext(request))


def submit_issue(request, project_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    can_view, can_edit, can_comment = utils.check_perms(request, project)
    if request.user.id:
        try:
            profile = request.user.userprofile
            profile_id = profile.id
        except AttributeError:
            profile_id = None
    else:
        profile_id = None
    if can_comment is False:
        return HttpResponseNotFound()
    else:
        if request.method == "POST":
            form = forms.IssueForm(project.id, can_edit, request.POST)
            if form.is_valid():
                issue = form.save()
                return HttpResponseRedirect(issue.get_absolute_url())
        else:
            if request.user:
                form = forms.IssueForm(project.id, can_edit, 
                    initial={ 'project': project.id, 'created_by': profile_id})
            else:
                form = forms.IssueForm(project.id, can_edit,
                    initial={ 'project': project.id })
        return render_to_response(
            "djtracker/submit_issue.html", locals(),
            context_instance=RequestContext(request))

def modify_issue(request, project_slug, issue_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    issue = get_object_or_404(models.Issue, slug=issue_slug)
    can_view, can_edit, can_comment = utils.check_perms(request, project)    
    if can_edit is False:
        return HttpResponseNotFound()
    else:
        if request.method == "POST":
            form = forms.IssueForm(project.id, can_edit, request.POST, instance=issue)
            if form.is_valid():
                issue=form.save()
                return HttpResponseRedirect(issue.get_absolute_url())
        else:
            form = forms.IssueForm(project.id, can_edit, instance=issue)
        
        return render_to_response(
            "djtracker/modify_issue.html", locals(),
            context_instance=RequestContext(request))

def view_issue(request, project_slug, issue_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    issue = get_object_or_404(models.Issue, slug=issue_slug)
    can_view, can_edit, can_comment = utils.check_perms(request, project)

    ## Check if we're watching
    is_watching = False
    if request.user.is_authenticated():
        try:
            profile = models.UserProfile.objects.get(user=request.user)
        except ObjectDoesNotExist:
            is_watching = False
            profile = None
        if profile in issue.watched_by.all():
            is_watching = True

    ## Check for GET variables
    if "watch" in request.GET and can_view:
        if request.GET['watch'] == "yes":
            try:
                profile = models.UserProfile.objects.get(user=request.user)
            except ObjectDoesNotExist:
                profile = models.UserProfile.create(user=request.user)
                profile.save()
            issue.watched_by.add(profile)
            return HttpResponseRedirect(
                reverse("project_issue", args=[project.slug, issue.slug])
            )
        elif request.GET['watch'] == "no":
            profile = models.UserProfile.objects.get(user=request.user)
            issue.watched_by.remove(profile)
            return HttpResponseRedirect(
                reverse("project_issue", args=[project.slug, issue.slug])
            )
                
    ## Check if we can view
    if can_view is False: 
        return HttpResponseNotFound()
    else:
        return render_to_response(
            "djtracker/issue_detail.html", locals(),
            context_instance=RequestContext(request))

def issue_attach(request, project_slug, issue_slug):
    project = get_object_or_404(models.Project, slug=project_slug)
    issue = get_object_or_404(models.Issue, slug=issue_slug)
    can_view, can_edit, can_comment = utils.check_perms(request, project)

    if can_view is False or can_comment is False: 
        return HttpResponseNotFound()
    else:
        if request.method == "POST":
            form = forms.FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(
                    issue.get_absolute_url()
                )
        else:
            form = forms.FileUploadForm(initial={'issue': issue.id})
    return render_to_response(
        "djtracker/upload_form.html", locals(),
        context_instance=RequestContext(request))

def view_profile(request, username):
    user = User.objects.get(username=username)
    profile = user.userprofile
    assigned_issues = []
    created_issues = []
    for x in profile.issue_set.all():
        can_view, can_edit, can_comment = utils.check_perms(request, x.project)
        if can_view:
            assigned_issues.append(x.id)

    for x in profile.issue_creator.all():
        can_view, can_edit, can_comment = utils.check_perms(request, x.project)
        if can_view:
            created_issues.append(x.id)

    assigned = models.Issue.objects.filter(id__in=assigned_issues)
    created = models.Issue.objects.filter(id__in=created_issues)

    return render_to_response(
        "djtracker/user_profile.html", locals(),
        context_instance=RequestContext(request))

def view_users(request):
    users = models.UserProfile.objects.all()
    return list_detail.object_list(request,
        queryset=users,
        paginate_by=20,
        template_name="djtracker/user_list.html",
        template_object_name="user"
    )

