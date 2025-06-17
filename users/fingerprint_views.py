from .fingerprint_utils import DPFJ_FMD_ANSI_378_2004
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from .models import User
from .fingerprint_utils import Fingerprint

@csrf_exempt
def fingerprint_login(request):
    if request.method == 'POST':
        fingerprint_data = request.POST.get('fingerprint_data')
        if fingerprint_data:
            try:
                fingerprint = Fingerprint()
                users = User.objects.all()
                
                for user in users:
                    fingerprints = [
                        user.fingerprint_id_thumb,
                        user.fingerprint_id_index,
                        user.fingerprint_id_middle,
                        user.fingerprint_id_ring,
                        user.fingerprint_id_little,
                    ]
                    fmds = [fp for fp in fingerprints if fp is not None]

                    if not fmds:
                        continue

                    matched_index = fingerprint.identify_finger(fmds, fingerprint_data)

                    if matched_index is not None:
                        login(request, user)
                        return redirect('reconciliation:main_dashboard_overview')

                messages.error(request, 'Fingerprint not recognized.')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, 'No fingerprint data received.')

    return render(request, 'users/fingerprint_login.html')

import base64
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import FingerprintRegistrationForm
from .models import User

@login_required
def register_fingerprint(request):
    if request.method == 'POST':
        form = FingerprintRegistrationForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            fingerprint_data = request.POST.get('fingerprint_data')
            finger_type = request.POST.get('finger_type')

            if fingerprint_data and finger_type:
                try:
                    # The data is Base64 encoded, but might have URL-safe characters
                    # Replace them and add padding if necessary
                    fingerprint_data = fingerprint_data.replace('-', '+').replace('_', '/')
                    padding = len(fingerprint_data) % 4
                    if padding:
                        fingerprint_data += '=' * (4 - padding)
                    
                    decoded_fingerprint = base64.b64decode(fingerprint_data)

                    setattr(user, f'fingerprint_id_{finger_type}', decoded_fingerprint)
                    user.save()
                    messages.success(request, f'{finger_type.capitalize()} fingerprint registered for {user.username}.')
                    return redirect('users:register_fingerprint')
                except Exception as e:
                    messages.error(request, f'Error saving fingerprint: {e}')
            else:
                messages.error(request, 'No fingerprint data or finger type received.')
    else:
        form = FingerprintRegistrationForm()
    
    user_id = request.GET.get('user_id')
    if user_id:
        user = User.objects.get(pk=user_id)
        return render(request, 'users/register_fingerprint.html', {'form': form, 'user': user})

    return render(request, 'users/register_fingerprint.html', {'form': form})