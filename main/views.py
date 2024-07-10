from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse,HttpResponse
from .models import Person,SpouseInfo, Family, UserRegistration, ContactMessage
from .forms import FamilyForm, PersonForm, SpouseInfoForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
import random, smtplib, ssl
import certifi
from django.db import IntegrityError
from django.core.mail import EmailMessage
# This view renders the tree.html template
def render_tree_view(request):
    return render(request, 'tree.html')

# Generate tree data starting from a person
def generate_tree_data(person):
    data = {
        "name": person.name,
        "id": person.id,
        "gender": person.gender,
        "children": []
    }
    
    # Find families where the person is the father
    families_as_father = Family.objects.filter(father=person)
    for family in families_as_father:
        children = family.children.filter(gender='M')
        for child in children:
            data["children"].append(generate_tree_data(child))

    # Find families where the person is the mother
    families_as_mother = Family.objects.filter(mother=person)
    for family in families_as_father & families_as_mother:
        # Get children who are sons (assuming male children)
        sons = family.children.filter(gender='M')
        for son in sons:
            # Recursively generate data for each child
            data["children"].append(generate_tree_data(son))
    return data

# This view generates data for D3.js collapsible tree
def get_tree_data(request):
    try:
        root_person = Person.objects.get(name="Anandsinhji")
    except Person.DoesNotExist:
        return JsonResponse({"error": "Root person not found"}, status=404)
    tree_data = generate_tree_data(root_person)
    return JsonResponse(tree_data)

def d3_collapsible_tree(request):
    try:
        root_person = Person.objects.get(name="Anandsinhji")
    except Person.DoesNotExist:
        return JsonResponse({"error": "Root person not found"}, status=404)
    tree_data = generate_tree_data(root_person)
    return JsonResponse(tree_data)

# This view displays details of a person

def person_detail(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    families = Family.objects.filter(father=person).prefetch_related('children')
    spouses = person.spouses.all()
    children_count = sum(family.children.count() for family in families)
    family_as_child = Family.objects.filter(children=person).first()
    father = family_as_child.father if family_as_child else None
    mother = family_as_child.mother if family_as_child else None

    return render(request, 'person_detail.html', {
        'person': person,
        'families': families,
        'children_count': children_count,
        'spouses': spouses,
        'father': father,
        'mother': mother
    })

# This view displays details of a child

def child_detail(request, child_id):
    child = get_object_or_404(Person, pk=child_id)
    family = Family.objects.filter(children=child).first()
    father = family.father if family else None
    mother = family.mother if family else None
    spouses = child.spouses.all()
    families = Family.objects.filter(father=child).prefetch_related('children')
    families_as_mother = Family.objects.filter(mother=child).prefetch_related('children')
    # families = families_as_father | families_as_mother
    children_count_father = sum(family.children.count() for family in families)
    children_count_mother = sum(family.children.count() for family in families_as_mother)
    return render(request, 'child_detail.html', {
        'child': child,
        'father': father,
        'mother': mother,
        'spouses': spouses,
        'families': families,
        'families_as_mother': families_as_mother,
        'children_count_father': children_count_father,
        'children_count_mother': children_count_mother,
    })

def RegisterUserView(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email_id = request.POST.get('email_id')
        password = request.POST.get('password')
        
        # Create and save the user registration
        user_registration = UserRegistration(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            password=password
        )
        try:
            user_registration.save()
        except IntegrityError:
            error_message = "Email already registered. Please use a different email."
            return render(request, 'signup.html', {'error_message': error_message})
        # Prepare email details
        subject = 'Registered Successfully'
        message = (
            f'<!DOCTYPE html><html><head><title>Welcome to Rampara Genealogy</title></head>'
            '<body style="font-family: Arial, sans-serif; background-color: #f8f9fa; margin: 0; padding: 0;">'
            '<div style="max-width: 600px; margin: 0 auto; padding: 20px;">'
            '<h1 style="text-align: center; color: #333;">Welcome to Rampara Genealogy</h1>'
            f'<p style="text-align: center; font-size: 16px;">Dear {first_name} {last_name},</p>'
            '<p style="text-align: center; font-size: 16px;">Thank you for registering with Genealogy! We\'re thrilled to have you join our community.</p>'
            '<p style="text-align: center; font-size: 16px;">Your registration is now complete, and you\'re all set to explore our website.</p>'
            '<h2 style="text-align: center; color: #333; margin-top: 30px;">Here are a few highlights of what you can expect:</h2>'
            '<ol style="font-size: 16px; margin-left: 30px;">'
            '<li>You can see the family tree.</li>'
            '<li>You can see person details, child details, etc.</li>'
            '<li>You can also add person details, update person details, delete person details.</li>'
            '<li>You can also add spouse details, update spouse details, delete spouse details.</li>'
            '<li>You can also add child details, update child details, delete child details.</li>'
            '</ol>'
            '<p style="text-align: center; font-size: 16px;">Start exploring now and make the most of your journey with us!</p>'
            '<p style="text-align: center; font-size: 16px;">Have a great day ☺️ </p>'
            '<p style="text-align: center; font-size: 16px; margin-top: 30px;">Warm regards,<br>Rampara Genealogy Team</p>'
            '</div></body></html>'
        )
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email_id]        
        # Create email message
        email = EmailMessage(subject, message, email_from, recipient_list)
        email.content_subtype = 'html'  # Set the email content type to HTML
        try:
            email.send()
        except Exception as e:
            print("Error sending email:", e)
        return redirect('login')
    return render(request, 'signup.html')


def LoginUserView(request):
    if request.method == 'POST':
        email = request.POST.get('email_id')
        passwordobj = request.POST.get('password')      
        user_registration = UserRegistration.objects.filter(email_id=email, password=passwordobj).last()
        if user_registration is not None:
            if user_registration.password == passwordobj:
                request.session['email'] = email
                return redirect('tree_view')
            else:
                return render(request, 'login.html', {'error_message': 'Invalid password'})  
        else:
            return render(request, 'login.html', {'error_message': 'User not found'})
    return render(request, 'login.html')

@login_required(login_url='/')
def logout_view(request):
    logout(request)
    return redirect('login')

def contactus_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        message = request.POST['message']
        ContactMessage.objects.create(name=name, email=email, phone=phone, message=message)
        return redirect('contactus')
    return render(request, 'contactus.html')


# Create a new person

def create_person(request):
    if request.method == 'POST':
        person_form = PersonForm(request.POST)
        if person_form.is_valid() :
            person_form.save()
        return redirect('create_spouse')
    else:
        person_form = PersonForm()
    return render(request, 'person_form.html', {'person_form': person_form})


def create_spouse(request):
    if request.method == 'POST':
        spouse_form = SpouseInfoForm(request.POST)
        if spouse_form.is_valid():
            spouse_form.save()
            return redirect('create_family')
    else:
        spouse_form = SpouseInfoForm()
    return render(request, 'spouse_form.html',{'spouse_form':spouse_form})


def create_family(request):
    if request.method == 'POST':
        family_form = FamilyForm(request.POST)
        if family_form.is_valid():
            family = family_form.save()
            children_ids = request.POST.getlist('children')
            for child_id in children_ids:
                child = Person.objects.get(id=child_id)
                family.children.add(child)
            return redirect('tree_view')
    else:
        family_form = FamilyForm()
        # Filter the queryset for father and mother fields based on gender
        family_form.fields['father'].queryset = Person.objects.filter(gender='M')
        family_form.fields['mother'].queryset = Person.objects.filter(gender='F')
    return render(request, 'family_form.html', {'family_form': family_form})

# Update an existing person

def update_person(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    if request.method == 'POST':
        person_form = PersonForm(request.POST, instance=person)
        if person_form.is_valid():
            person_form.save()
            # Redirect to the update_spouse view with the spouse's ID
            return redirect('person_detail', person_id=person.id)
    else:
        person_form = PersonForm(instance=person)
    return render(request, 'person_edit_form.html', {'person_form': person_form})


def update_spouse(request, spouse_id):
    spouse = get_object_or_404(SpouseInfo, pk=spouse_id)
    if request.method == 'POST':
        spouse_form = SpouseInfoForm(request.POST, instance=spouse)
        if spouse_form.is_valid():
            spouse_form.save()
            # Redirect to the update_family view with the spouse's ID
            return redirect('tree_view')
    else:
        spouse_form = SpouseInfoForm(instance=spouse)
    return render(request, 'spouse_edit_form.html', {'spouse_form': spouse_form})


def update_family(request, family_id):
    family = get_object_or_404(Family, pk=family_id)
    if request.method == 'POST':
        family_form = FamilyForm(request.POST, instance=family)
        if family_form.is_valid():
            family_form.save()
            # Redirect to the family_detail view with the family's ID
            return redirect('tree_view')
    else:
        family_form = FamilyForm(instance=family)
    return render(request, 'family_edit_form.html', {'family_form': family_form})

# Delete a person

def delete_person(request, person_id):
    person = get_object_or_404(Person, pk=person_id)
    if request.method == 'POST':
        person.delete()
        return redirect('tree_view')
    return render(request, 'person_confirm_delete.html', {'person': person})


def delete_spouse(request, spouse_id):
    spouse = get_object_or_404(SpouseInfo, pk=spouse_id)
    if request.method == 'POST':
        spouse.delete()
        return redirect('tree_view')
    return render(request, 'spouse_confirm_delete.html', {'spouse': spouse})


def delete_family(request, family_id):
    family = get_object_or_404(Family, pk=family_id)
    if request.method == 'POST':
        family.delete()
        return redirect('tree_view')
    return render(request, 'family_confirm_delete.html', {'family': family})

def forgotpass(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        if not UserRegistration.objects.filter(email_id=email_id).exists():
            return render(request, 'getemail.html', {'error_message': "Email address not registered." "\n\n\n" "Please enter a valid email."})
        otp = ''.join(random.choices('1234567890', k=4))
        request.session['otp'] = otp
        # Create email content
        subject = "Your OTP Code"
        body = f"Your OTP code is: {otp}"
        message = f"Subject: {subject}\n\n{body}"
        try:
            # Use certifi's certificate bundle
            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login("ramparagenealogy@gmail.com", "pzkq adso icms rjed")
                server.sendmail("ramparagenealogy@gmail.com", email_id, message)
        except Exception as e:
            print("Error sending email:", e)
            return HttpResponse("Failed to send OTP email. Please try again.")
        request.session['email_id'] = email_id
        return redirect('otp')    
    return render(request, 'getemail.html')

def otp(request):
    if 'email_id' not in request.session:
        return redirect('login')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if not entered_otp:
            return render(request, 'otp.html')
        stored_otp = request.session.get('otp')
        if entered_otp == stored_otp:
            return redirect('changepass')
        else:
            return render(request, 'otp.html',{'error_message':'Wrong OTP Entered.'})
    return render(request, 'otp.html')


def changepass(request):
    if request.method == 'POST':
        new_password = request.POST.get('password')
        if not new_password:
            return render(request, 'changepass.html', {'error_message': "Password cannot be empty."})
        if 'email_id' not in request.session:
            return redirect('login')
        try:
            user = UserRegistration.objects.get(email_id=request.session['email_id'])
            user.password = new_password
            user.save()
            # Send email notification
            email = user.email_id
            subject = "Password Changed Successfully..."
            body = f"Hello,Your password has been successfully changed."
            message = f"Subject: {subject}\n\n{body}"
            try:
                # Use certifi's certificate bundle
                context = ssl.create_default_context(cafile=certifi.where())
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login("ramparagenealogy@gmail.com", "pzkq adso icms rjed")
                    server.sendmail("ramparagenealogy@gmail.com", email, message)
            except Exception as e:
                print("Error sending email:", e)
            return redirect('login')
        except UserRegistration.DoesNotExist:
            return redirect('login')
    return render(request, 'changepass.html')
