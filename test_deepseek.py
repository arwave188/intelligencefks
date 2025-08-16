#!/usr/bin/env python3
"""
Teste rápido do DeepSeek Local
Execute: python test_deepseek.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.deepseek_local import gerar_codigo, revisar_codigo, criar_projeto

def test_basic():
    """Teste básico de funcionamento."""
    print("🧪 Testando DeepSeek Local...")
    
    try:
        # Teste simples
        resultado = gerar_codigo(
            "Crie uma função Python para calcular o fatorial de um número",
            max_tokens=512,
            temperature=0.7
        )
        
        print("✅ Teste básico passou!")
        print(f"📝 Resultado: {resultado[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def test_code_review():
    """Teste de revisão de código."""
    print("\n🔍 Testando revisão de código...")
    
    codigo_exemplo = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    try:
        resultado = revisar_codigo(codigo_exemplo)
        print("✅ Revisão de código funcionou!")
        print(f"📝 Sugestões: {resultado[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Erro na revisão: {e}")
        return False

def test_project_creation():
    """Teste de criação de projeto."""
    print("\n🏗️ Testando criação de projeto...")
    
    try:
        resultado = criar_projeto(
            "API REST simples para gerenciar tarefas (CRUD)",
            "Python"
        )
        print("✅ Criação de projeto funcionou!")
        print(f"📝 Projeto: {resultado[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DeepSeek-Coder-V2.5 Local - Teste de Funcionalidades")
    print("📦 Modelo: DeepSeek-Coder-V2.5-Lite-Instruct (16B)")
    print("=" * 60)
    
    # Executar testes
    tests = [
        test_basic,
        test_code_review, 
        test_project_creation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Resultados: {passed}/{len(tests)} testes passaram")

    if passed == len(tests):
        print("🎉 Todos os testes passaram! DeepSeek-Coder-V2.5 está pronto para o RunPod!")
        print("🚀 Modelo de última geração carregado com sucesso!")
    else:
        print("⚠️ Alguns testes falharam. Verifique a configuração.")
