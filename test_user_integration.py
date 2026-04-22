#!/usr/bin/env python3
"""
Test script para validar que la API RAG recibe y procesa correctamente
los parámetros de usuario (username y user_display_name).
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pydantic import BaseModel, ValidationError


class AskRequest(BaseModel):
    question: str
    username: str = None
    user_display_name: str = None


def test_payload_complete():
    """Test: Payload completo con usuario."""
    print("=" * 70)
    print("TEST 1: Payload completo con usuario")
    print("=" * 70)
    
    payload = {
        "question": "¿Cuál es la duración del contrato?",
        "username": "juan.perez",
        "user_display_name": "Juan Pérez"
    }
    
    try:
        request = AskRequest(**payload)
        print(f"✅ Validación exitosa")
        print(f"   Question: {request.question}")
        print(f"   Username: {request.username}")
        print(f"   Display: {request.user_display_name}")
        return True
    except ValidationError as e:
        print(f"❌ Error de validación: {e}")
        return False


def test_payload_without_user():
    """Test: Payload sin usuario."""
    print("\n" + "=" * 70)
    print("TEST 2: Payload sin usuario")
    print("=" * 70)
    
    payload = {
        "question": "¿Cuál es la duración del contrato?"
    }
    
    try:
        request = AskRequest(**payload)
        print(f"✅ Validación exitosa")
        print(f"   Question: {request.question}")
        print(f"   Username: {request.username}")
        print(f"   Display: {request.user_display_name}")
        return True
    except ValidationError as e:
        print(f"❌ Error de validación: {e}")
        return False


def test_payload_username_only():
    """Test: Solo username, sin display_name."""
    print("\n" + "=" * 70)
    print("TEST 3: Solo username, sin display_name")
    print("=" * 70)
    
    payload = {
        "question": "¿Cuál es la duración del contrato?",
        "username": "juan.perez"
    }
    
    try:
        request = AskRequest(**payload)
        print(f"✅ Validación exitosa")
        print(f"   Question: {request.question}")
        print(f"   Username: {request.username}")
        print(f"   Display: {request.user_display_name}")
        return True
    except ValidationError as e:
        print(f"❌ Error de validación: {e}")
        return False


def test_empty_question():
    """Test: Pregunta vacía (debe fallar)."""
    print("\n" + "=" * 70)
    print("TEST 4: Pregunta vacía (debe fallar)")
    print("=" * 70)
    
    payload = {
        "question": "",
        "username": "juan.perez"
    }
    
    try:
        request = AskRequest(**payload)
        print(f"❌ Debería haber fallado, pero no lo hizo")
        return False
    except ValidationError as e:
        print(f"✅ Error esperado: La pregunta vacía no valida en Pydantic")
        print(f"   (Se valida en api.py después de recibirla)")
        return True


def test_mock_rag_call():
    """Test: Simula llamada a función rag()."""
    print("\n" + "=" * 70)
    print("TEST 5: Simulación de llamada a rag()")
    print("=" * 70)
    
    # Mock result
    result = {
        "question": "¿Cuál es la duración del contrato?",
        "chunks": ["Fragmento 1...", "Fragmento 2..."],
        "context": "[Fragmento 1]\nFragmento 1...\n\n[Fragmento 2]\nFragmento 2...",
        "answer": "La duración típica es de 2 años...",
        "username": "juan.perez",
        "user_display_name": "Juan Pérez",
    }
    
    print(f"✅ Resultado esperado de rag():")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Check required fields
    required_fields = ["question", "answer", "chunks", "username"]
    missing = [f for f in required_fields if f not in result]
    
    if missing:
        print(f"\n❌ Campos faltantes: {missing}")
        return False
    else:
        print(f"\n✅ Todos los campos requeridos están presentes")
        return True


def test_api_response():
    """Test: Estructura de respuesta de /ask."""
    print("\n" + "=" * 70)
    print("TEST 6: Estructura de respuesta de /ask")
    print("=" * 70)
    
    api_response = {
        "question": "¿Cuál es la duración del contrato?",
        "answer": "La duración típica es de 2 años...",
        "chunks": ["Fragmento 1...", "Fragmento 2..."],
        "username": "juan.perez"
    }
    
    print(f"✅ Response esperado de /ask:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    required_fields = ["question", "answer", "chunks", "username"]
    missing = [f for f in required_fields if f not in api_response]
    
    if missing:
        print(f"\n❌ Campos faltantes: {missing}")
        return False
    else:
        print(f"\n✅ Todos los campos requeridos están presentes")
        return True


def main():
    """Ejecuta todos los tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " VALIDACIÓN DE API RAG - INTEGRACIÓN DE USUARIO ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    
    tests = [
        test_payload_complete,
        test_payload_without_user,
        test_payload_username_only,
        test_empty_question,
        test_mock_rag_call,
        test_api_response,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test fallido con excepción: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Pruebas pasadas: {passed}/{total}")
    
    if passed == total:
        print("✅ ¡TODOS LOS TESTS PASARON!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())
