import uuid
import os
from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .models import Document, ChatLog
from .serializers import (
    ChatQuerySerializer, ChatResponseSerializer,
    DocumentUploadSerializer, DocumentSerializer, ChatLogSerializer
)
from .rag_engine import get_rag_engine

class ChatView(APIView):
    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            session_id = serializer.validated_data.get('session_id', str(uuid.uuid4()))
            
            # Get RAG engine
            rag = get_rag_engine()
            
            # Detect language
            language = rag.detect_language(query)
            
            # Generate response
            response_text, confidence = rag.generate_response(query, language)
            
            # Log the conversation
            ChatLog.objects.create(
                session_id=session_id,
                query=query,
                response=response_text,
                language=language,
                confidence_score=confidence
            )
            
            response_data = {
                'response': response_text,
                'language': language,
                'confidence': confidence,
                'session_id': session_id
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentUploadView(APIView):
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            title = serializer.validated_data['title']
            uploaded_file = serializer.validated_data['file']
            
            # Save file to documents directory
            os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
            file_path = os.path.join(settings.DOCUMENTS_DIR, uploaded_file.name)
            
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Create document record
            doc = Document.objects.create(
                title=title,
                file_path=file_path,
                content_hash="",  # Will be updated during processing
                processed=False
            )
            
            # Process document with RAG engine
            try:
                rag = get_rag_engine()
                chunks = rag.doc_processor.process_document(file_path)
                if chunks:
                    rag._add_chunks_to_db(chunks)
                    doc.processed = True
                    doc.content_hash = rag.doc_processor.get_file_hash(file_path)
                    doc.save()
                    
                    return Response({
                        'message': f'Document "{title}" uploaded and processed successfully.',
                        'chunks_created': len(chunks)
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': 'Failed to process document content.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                return Response({
                    'error': f'Error processing document: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentListView(APIView):
    def get(self, request):
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)

class InitializeKnowledgeBaseView(APIView):
    def post(self, request):
        """Initialize knowledge base with documents from documents directory"""
        try:
            rag = get_rag_engine()
            added_count = rag.add_documents(str(settings.DOCUMENTS_DIR))
            
            return Response({
                'message': f'Knowledge base initialized. {added_count} documents processed.',
                'documents_added': added_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Error initializing knowledge base: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteLogsView(APIView):
    def delete(self, request):
        session_id = request.query_params.get('session_id')
        
        if session_id:
            deleted_count = ChatLog.objects.filter(session_id=session_id).delete()[0]
            return Response({
                'message': f'Deleted {deleted_count} logs for session {session_id}'
            }, status=status.HTTP_200_OK)
        else:
            # Delete all logs (admin function)
            deleted_count = ChatLog.objects.all().delete()[0]
            return Response({
                'message': f'Deleted all {deleted_count} chat logs'
            }, status=status.HTTP_200_OK)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        # Check if Ollama is running
        import requests
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        ollama_status = response.status_code == 200
    except:
        ollama_status = False
    
    return Response({
        'status': 'healthy',
        'ollama_connected': ollama_status,
        'model': settings.OLLAMA_MODEL,
        'documents_count': Document.objects.count(),
        'chat_logs_count': ChatLog.objects.count()
    })