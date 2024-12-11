from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from login.models import JobSeeker, new_user, CompanyInCharge, UniversityInCharge
from .models import Message, MessageAttachment
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max


MODEL_MAPPING = {
    "JobSeeker": JobSeeker,
    "UniversityInCharge": UniversityInCharge,
    "CompanyInCharge": CompanyInCharge,
    "new_user": new_user,
}

@api_view(['POST'])
@permission_classes([AllowAny])
def send_chat(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authorization header is missing or invalid'}, status=400)

    token = auth_header.split(' ')[1]
    sender_model = request.data.get("sender_model")
    sender_email = request.data.get("sender_email")

    if not sender_model or sender_model not in MODEL_MAPPING:
        return JsonResponse({"error": "Invalid sender_model"}, status=400)
    if not sender_email:
        return JsonResponse({"error": "Sender email is required"}, status=400)

    sender_model_class = MODEL_MAPPING[sender_model]

    try:
        sender = sender_model_class.objects.filter(token=token).get(
            **{"email": sender_email} if hasattr(sender_model_class, "email") else {"official_email": sender_email}
        )
        print(f"Sender verified: {sender}")
    except ObjectDoesNotExist:
        print(f"Sender not found: email={sender_email}, token={token}, model={sender_model}")
        return JsonResponse({'error': 'Invalid token or sender not found'}, status=401)

    recipient_email = request.data.get("recipient_email")
    recipient_model = request.data.get("recipient_model")
    content = request.data.get("content", "").strip() or ""
    subject = request.data.get("subject", "").strip() or "" 

    if not all([recipient_email, recipient_model]):
        return JsonResponse({"error": "Recipient email and recipient model are required"}, status=400)

    if recipient_model not in MODEL_MAPPING:
        return JsonResponse({"error": "Invalid recipient_model"}, status=400)

    recipient_model_class = MODEL_MAPPING[recipient_model]

    try:
        recipient = recipient_model_class.objects.get(
            **{"email": recipient_email} if hasattr(recipient_model_class, "email") else {"official_email": recipient_email}
        )
        print(f"Recipient verified: {recipient}")
    except ObjectDoesNotExist:
        print(f"Recipient not found: email={recipient_email}, model={recipient_model}")
        return JsonResponse({"error": "Recipient not found in the specified model"}, status=404)

    if not content and 'attachments' not in request.FILES:
        return JsonResponse({"error": "Either content or attachments must be provided"}, status=400)

    try:
        message = Message.objects.create(
            sender_email=sender_email,
            recipient_email=recipient_email,
            sender_model=sender_model,
            recipient_model=recipient_model,
            subject=subject,
            content=content
        )

        if 'attachments' in request.FILES:
            attachment_files = request.FILES.getlist('attachments')
            for uploaded_file in attachment_files:
                attachment = MessageAttachment.objects.create(
                    file=uploaded_file,
                    original_name=uploaded_file.name,
                    file_type=uploaded_file.content_type
                )
                message.attachments.add(attachment)  

        return Response({
            "message": "Message sent successfully",
            "data": {
                "id": message.id,
                "sender_email": sender_email,
                "recipient_email": recipient_email,
                "sender_model": sender_model,
                "recipient_model": recipient_model,
                "subject": subject,
                "content": content,
                "attachments": [
                    {
                        "original_name": attachment.original_name,
                        "file_url": attachment.file.url 
                    }
                    for attachment in message.attachments.all()
                ],
                "timestamp": message.timestamp
            }
        })
    except Exception as e:
        print(f"Error creating message: {str(e)}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_messages(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authorization header is missing or invalid'}, status=400)

    token = auth_header.split(' ')[1]
    sender_model = request.query_params.get("sender_model")
    sender_email = request.query_params.get("sender_email")
    recipient_model = request.query_params.get("recipient_model")
    recipient_email = request.query_params.get("recipient_email")

    if not all([sender_model, sender_email, recipient_model, recipient_email]):
        return JsonResponse({"error": "All parameters are required (sender_model, sender_email, recipient_model, recipient_email)"}, status=400)

    if sender_model not in MODEL_MAPPING or recipient_model not in MODEL_MAPPING:
        return JsonResponse({"error": "Invalid sender_model or recipient_model"}, status=400)

    sender_model_class = MODEL_MAPPING[sender_model]
    recipient_model_class = MODEL_MAPPING[recipient_model]

    try:
        sender = sender_model_class.objects.filter(token=token).get(
            **{"email": sender_email} if hasattr(sender_model_class, "email") else {"official_email": sender_email}
        )
        print(f"Sender verified: {sender}")
    except ObjectDoesNotExist:
        print(f"Sender not found: email={sender_email}, token={token}, model={sender_model}")
        return JsonResponse({'error': 'Invalid token or sender not found'}, status=401)

    try:
        recipient = recipient_model_class.objects.get(
            **{"email": recipient_email} if hasattr(recipient_model_class, "email") else {"official_email": recipient_email}
        )
        print(f"Recipient verified: {recipient}")
    except ObjectDoesNotExist:
        print(f"Recipient not found: email={recipient_email}, model={recipient_model}")
        return JsonResponse({'error': 'Recipient not found in the specified model'}, status=404)

    try:
        messages = Message.objects.filter(
            (Q(sender_email=sender_email) & Q(recipient_email=recipient_email)) |
            (Q(sender_email=recipient_email) & Q(recipient_email=sender_email))
        ).order_by('timestamp')

        messages_data = []
        for message in messages:
            attachments = message.attachments.all()  
            attachments_data = [
                {
                    "original_name": attachment.original_name,
                    "file_url": attachment.file.url  
                }
                for attachment in attachments
            ]

            messages_data.append({
                "id": message.id,
                "sender_email": message.sender_email,
                "recipient_email": message.recipient_email,
                "sender_model": message.sender_model,
                "recipient_model": message.recipient_model,
                "subject": message.subject,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "attachments": attachments_data 
            })

        return JsonResponse({
            "message": "Chat retrieved successfully",
            "data": messages_data
        }, status=200)

    except Exception as e:
        print(f"Error fetching chat: {str(e)}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

@api_view(['GET'])
def search_user(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "Search query cannot be empty"}, status=400)

    result = []
    for model_name, model_class in MODEL_MAPPING.items():
        try:
            if model_name == "User":
                queryset = model_class.objects.filter(username__icontains=query)
            elif model_name == "JobSeeker":
                queryset = model_class.objects.filter(
                    Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
                )
            elif model_name == "UniversityInCharge":
                queryset = model_class.objects.filter(
                    Q(university_name__icontains=query) | Q(official_email__icontains=query)
                )
            elif model_name == "CompanyInCharge":
                queryset = model_class.objects.filter(
                    Q(company_name__icontains=query) | Q(company_person_name__icontains=query) | Q(official_email__icontains=query)
                )
            elif model_name == "new_user":
                queryset = model_class.objects.filter(
                    Q(firstname__icontains=query) | Q(lastname__icontains=query) | Q(email__icontains=query)
                )
            else:
                continue

            for instance in queryset:
                user_data = {
                    "id": instance.id,
                    "model": model_name,
                    "email": getattr(instance, 'email', getattr(instance, 'official_email', None)),
                }

                if model_name == "User":
                    user_data["username"] = instance.username
                    user_data["name"] = getattr(instance, 'first_name', '') + " " + getattr(instance, 'last_name', '')
                elif model_name == "JobSeeker":
                    user_data["name"] = instance.first_name + " " + instance.last_name
                elif model_name == "UniversityInCharge":
                    user_data["name"] = instance.university_name
                elif model_name == "CompanyInCharge":
                    user_data["name"] = instance.company_name
                elif model_name == "new_user":
                    user_data["name"] = instance.firstname + " " + instance.lastname

                result.append(user_data)

        except Exception as e:
            print(f"Error searching in {model_name}: {e}")
            continue

    return Response(result)

@api_view(['GET'])
@permission_classes([AllowAny])
def inbox(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Authorization header is missing or invalid'}, status=400)

    token = auth_header.split(' ')[1]

    user_model = request.query_params.get("user_model")
    user_email = request.query_params.get("user_email")

    if not user_model or user_model not in MODEL_MAPPING:
        return JsonResponse({"error": "Invalid or missing user_model"}, status=400)
    if not user_email:
        return JsonResponse({"error": "user_email is required"}, status=400)

    user_model_class = MODEL_MAPPING[user_model]

    try:
        user = user_model_class.objects.filter(token=token).get(
            **{"email": user_email} if hasattr(user_model_class, "email") else {"official_email": user_email}
        )
        print(f"User verified: {user}")
    except ObjectDoesNotExist:
        print(f"User not found: email={user_email}, token={token}, model={user_model}")
        return JsonResponse({'error': 'Invalid token or user not found'}, status=401)

    try:
        subquery = Message.objects.filter(
            Q(sender_email=user_email) | Q(recipient_email=user_email)
        ).values(
            'sender_email', 'recipient_email'
        ).annotate(latest_message_id=Max('id'))

        latest_message_ids = [entry['latest_message_id'] for entry in subquery]
        messages = Message.objects.filter(id__in=latest_message_ids).order_by('-timestamp')

        inbox_data = []
        seen_conversations = set()

        for message in messages:
            if message.sender_email == user_email:
                conversation_with = message.recipient_email
                conversation_model = message.recipient_model
            else:
                conversation_with = message.sender_email
                conversation_model = message.sender_model

            if conversation_with in seen_conversations:
                continue

            seen_conversations.add(conversation_with)

            inbox_data.append({
                "conversation_with": conversation_with,
                "conversation_model": conversation_model,
                "subject": message.subject,
                "latest_message": message.content,
                "timestamp": message.timestamp,
            })

        return JsonResponse({
            "message": "Inbox retrieved successfully",
            "data": inbox_data
        }, status=200)
    except Exception as e:
        print(f"Error fetching inbox: {str(e)}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
