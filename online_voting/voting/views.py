from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views import View
from .models import VotingEvent, Candidate, Vote, Category

# voting/views.py

from .forms import (
    ProfileUpdateForm,
    UserUpdateForm,
    VotingEventForm,
    CandidateForm,
    RegisterForm,
    Profile,
)


# Generate a unique token for private events
def generate_unique_token():
    while True:
        token = get_random_string(10)
        if not VotingEvent.objects.filter(event_token=token).exists():
            return token


# Create a new voting event
@login_required
def create_event(request):
    CandidateFormSet = modelformset_factory(Candidate, form=CandidateForm, extra=1)
    if request.method == "POST":
        event_form = VotingEventForm(request.POST)
        candidate_formset = CandidateFormSet(request.POST, request.FILES)
        if event_form.is_valid() and candidate_formset.is_valid():
            voting_event = event_form.save(commit=False)
            voting_event.created_by = request.user
            if voting_event.is_private:
                voting_event.event_token = generate_unique_token()
            else:
                voting_event.event_token = "0000"
            voting_event.save()
            selected_categories = event_form.cleaned_data["categories"]
            voting_event.categories.set(selected_categories)
            for form in candidate_formset:
                candidate = form.save(commit=False)
                candidate.voting_event = voting_event
                candidate.save()
            return redirect("voting:event_detail", event_id=voting_event.id)
    else:
        event_form = VotingEventForm()
        candidate_formset = CandidateFormSet(queryset=Candidate.objects.none())

    return render(
        request,
        "voting/create_event.html",
        {
            "event_form": event_form,
            "candidate_formset": candidate_formset,
        },
    )


# View event details
@login_required()
def event_detail(request, event_id):
    voting_event = get_object_or_404(VotingEvent, id=event_id)
    candidates = voting_event.candidates.all()
    user_vote = Vote.objects.filter(voting_event=voting_event,voter= request.user).first()
    voted_candidate =user_vote.candidate if user_vote else None
    
    
    return render(
        request,
        "voting/event_detail.html",
        {"event": voting_event, "candidates": candidates, "voted_candidate": voted_candidate},
    )


# Vote on an event
@login_required
def vote(request, event_id):
    event = get_object_or_404(VotingEvent, pk=event_id)

    # Check if the user has already voted for this event
    if Vote.objects.filter(voting_event=event, voter=request.user).exists():
        messages.error(request, "You have already voted for this event!")
        return redirect("voting:event_detail", event_id=event.id)

    if request.method == "POST":
        candidate_id = request.POST.get("candidate")
        if candidate_id:
            candidate = get_object_or_404(Candidate, pk=candidate_id)

            # Save the vote with the voter information
            vote = Vote(candidate=candidate, voting_event=event, voter=request.user)

            # Set the vote as anonymous if the event is private
            if event.is_private:
                vote.is_anonymous = True

            vote.save()
            messages.success(request, "Your vote has been cast successfully!")
            return redirect("voting:vote_result", event_id=event.id)

    return redirect("voting:event_detail", event_id=event.id)


# View voting results
def vote_result(request, event_id):
    voting_event = get_object_or_404(VotingEvent, id=event_id)
    candidates = voting_event.candidates.all()
    now = timezone.now()
    return render(
        request,
        "voting/vote_result.html",
        {"event": voting_event, "candidates": candidates, "now": now},
    )


# See events by filtering them
def event_list(request):
    now = timezone.now()
    ongoing_events = VotingEvent.objects.filter(start_time__lte=now, end_time__gte=now)
    upcoming_events = VotingEvent.objects.filter(start_time__gt=now)
    previous_events = VotingEvent.objects.filter(end_time__lt=now)

    categories = Category.objects.all()

    context = {
        "ongoing_events": ongoing_events,
        "upcoming_events": upcoming_events,
        "previous_events": previous_events,
        "categories": categories,
    }

    return render(request, "voting/home.html", context)


# Events created by user
@login_required
def my_events(request):
    events = VotingEvent.objects.filter(created_by=request.user)
    return render(request, "voting/myevent.html", {"events": events})


# Update profile
@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("voting:profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(
        request,
        "voting/profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


# Registration view
class RegistrationView(View):
    form_class = RegisterForm
    template_name = "voting/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("voting:event_list")  # Redirect authenticated users
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # Redirect to login after successful registration
        return render(request, self.template_name, {"form": form})


# Login view
class LoginView(View):
    template_name = "voting/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("voting:event_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")  # Get the value of 'remember' checkbox

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Set session expiration based on 'remember' checkbox
            if remember:
                request.session.set_expiry(1209600)  # Set session to 2 weeks
            else:
                request.session.set_expiry(0)  # Set session to expire at browser close

            return redirect(
                "voting:event_list"
            )  # Redirect to a success page or home page
        else:
            messages.error(request, "Invalid username or password")

        return render(request, self.template_name)


# Filter by category
def event_by_category(request, cate):
    category = get_object_or_404(Category, name=cate)
    events = VotingEvent.objects.filter(categories=category)
    return render(
        request,
        "voting/event_list.html",
        {"events": events, "selected_category": category},
    )
