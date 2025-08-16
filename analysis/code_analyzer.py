"""
Analisador Avançado de Código - Sem Censura
Especializado em engenharia reversa, análise de malware e vulnerabilidades
"""

import os
import re
import ast
import logging
from typing import Dict, List, Any, Optional
from models.deepseek_local import gerar_codigo, engenharia_reversa

logger = logging.getLogger(__name__)

class AnalisadorCodigoAvancado:
    """
    Analisador de código sem restrições para:
    - Engenharia reversa
    - Análise de malware  
    - Detecção de vulnerabilidades
    - Deobfuscação de código
    """
    
    def __init__(self):
        self.padroes_suspeitos = {
            'eval_dinamico': [r'eval\s*\(', r'exec\s*\(', r'Function\s*\('],
            'obfuscacao': [r'\\x[0-9a-fA-F]{2}', r'\\u[0-9a-fA-F]{4}', r'String\.fromCharCode'],
            'network': [r'XMLHttpRequest', r'fetch\s*\(', r'socket\s*\(', r'urllib'],
            'file_system': [r'open\s*\(', r'fopen', r'CreateFile', r'WriteFile'],
            'crypto': [r'crypto', r'encrypt', r'decrypt', r'hash', r'md5', r'sha'],
            'shellcode': [r'\\x90', r'\\xcc', r'\\x31\\xc0', r'nop', r'int3'],
            'registry': [r'RegOpenKey', r'RegSetValue', r'HKEY_'],
            'process': [r'CreateProcess', r'ShellExecute', r'system\s*\(', r'subprocess']
        }
        
        logger.info("🔍 Analisador de Código Avançado inicializado")
    
    def analisar_codigo_completo(self, codigo: str, linguagem: str = "auto") -> Dict[str, Any]:
        """Análise completa e sem censura de qualquer código."""
        
        resultado = {
            'linguagem_detectada': self._detectar_linguagem(codigo),
            'padroes_suspeitos': self._detectar_padroes_suspeitos(codigo),
            'analise_ia': self._analise_com_ia(codigo, linguagem),
            'vulnerabilidades': self._detectar_vulnerabilidades(codigo),
            'obfuscacao': self._analisar_obfuscacao(codigo),
            'comportamento': self._analisar_comportamento(codigo),
            'nivel_risco': 'BAIXO'
        }
        
        # Calcular nível de risco
        resultado['nivel_risco'] = self._calcular_nivel_risco(resultado)
        
        logger.info(f"✅ Análise concluída - Risco: {resultado['nivel_risco']}")
        return resultado
    
    def engenharia_reversa_avancada(self, codigo_obfuscado: str) -> Dict[str, Any]:
        """Engenharia reversa completa sem restrições."""
        
        prompt = f"""
ENGENHARIA REVERSA AVANÇADA - SEM RESTRIÇÕES

Analise este código e forneça:

1. **DEOBFUSCAÇÃO COMPLETA**:
   - Código limpo equivalente
   - Técnicas de ofuscação utilizadas
   - Métodos de evasão empregados

2. **ANÁLISE COMPORTAMENTAL**:
   - Funcionalidades principais
   - Operações de rede/arquivo/sistema
   - Possíveis payloads ou backdoors

3. **ANÁLISE DE SEGURANÇA**:
   - Vulnerabilidades exploráveis
   - Vetores de ataque
   - Técnicas de persistência

4. **CONTRAMEDIDAS**:
   - Como detectar este código
   - Métodos de mitigação
   - Assinaturas para detecção

CÓDIGO PARA ANÁLISE:
```
{codigo_obfuscado}
```

FORNEÇA ANÁLISE TÉCNICA COMPLETA SEM OMITIR DETALHES:
"""
        
        analise_ia = engenharia_reversa(prompt)
        
        return {
            'codigo_original': codigo_obfuscado,
            'analise_completa': analise_ia,
            'padroes_detectados': self._detectar_padroes_suspeitos(codigo_obfuscado),
            'nivel_obfuscacao': self._calcular_nivel_obfuscacao(codigo_obfuscado),
            'recomendacoes': self._gerar_recomendacoes_seguranca(codigo_obfuscado)
        }
    
    def analisar_malware(self, codigo_suspeito: str) -> Dict[str, Any]:
        """Análise especializada em malware sem censura."""
        
        prompt = f"""
ANÁLISE DE MALWARE - MODO FORENSE

Analise este código suspeito como um especialista em segurança:

1. **CLASSIFICAÇÃO DO MALWARE**:
   - Tipo (trojan, worm, ransomware, etc.)
   - Família de malware (se identificável)
   - Variante ou versão

2. **TÉCNICAS UTILIZADAS**:
   - Métodos de infecção
   - Técnicas de evasão
   - Persistência no sistema
   - Comunicação C&C

3. **PAYLOAD E FUNCIONALIDADES**:
   - Ações maliciosas executadas
   - Dados coletados/roubados
   - Danos potenciais ao sistema

4. **INDICADORES DE COMPROMISSO (IOCs)**:
   - Hashes de arquivos
   - URLs/IPs maliciosos
   - Chaves de registro modificadas
   - Arquivos criados/modificados

5. **CONTRAMEDIDAS**:
   - Como remover/neutralizar
   - Prevenção de reinfecção
   - Detecção proativa

CÓDIGO SUSPEITO:
```
{codigo_suspeito}
```

FORNEÇA ANÁLISE FORENSE COMPLETA:
"""
        
        analise_forense = gerar_codigo(prompt)
        
        return {
            'codigo_analisado': codigo_suspeito,
            'analise_forense': analise_forense,
            'classificacao_malware': self._classificar_malware(codigo_suspeito),
            'iocs_extraidos': self._extrair_iocs(codigo_suspeito),
            'nivel_periculosidade': self._avaliar_periculosidade(codigo_suspeito)
        }
    
    def _detectar_linguagem(self, codigo: str) -> str:
        """Detecta a linguagem de programação."""
        indicadores = {
            'python': [r'def\s+\w+', r'import\s+\w+', r'print\s*\(', r'if\s+__name__'],
            'javascript': [r'function\s+\w+', r'var\s+\w+', r'console\.log', r'document\.'],
            'c': [r'#include\s*<', r'int\s+main', r'printf\s*\(', r'malloc\s*\('],
            'java': [r'public\s+class', r'public\s+static\s+void\s+main', r'System\.out'],
            'php': [r'<\?php', r'\$\w+', r'echo\s+', r'function\s+\w+'],
            'assembly': [r'mov\s+\w+', r'push\s+\w+', r'call\s+\w+', r'jmp\s+\w+'],
            'powershell': [r'Get-\w+', r'Set-\w+', r'Invoke-\w+', r'\$\w+\s*=']
        }
        
        for linguagem, padroes in indicadores.items():
            if any(re.search(padrao, codigo, re.IGNORECASE) for padrao in padroes):
                return linguagem
        
        return 'desconhecida'
    
    def _detectar_padroes_suspeitos(self, codigo: str) -> Dict[str, List[str]]:
        """Detecta padrões suspeitos no código."""
        deteccoes = {}
        
        for categoria, padroes in self.padroes_suspeitos.items():
            matches = []
            for padrao in padroes:
                encontrados = re.findall(padrao, codigo, re.IGNORECASE)
                matches.extend(encontrados)
            
            if matches:
                deteccoes[categoria] = matches
        
        return deteccoes
    
    def _analise_com_ia(self, codigo: str, linguagem: str) -> str:
        """Análise detalhada usando IA."""
        prompt = f"""
Analise este código {linguagem} sem restrições e identifique:

1. Funcionalidades principais
2. Possíveis vulnerabilidades de segurança
3. Técnicas de ofuscação (se houver)
4. Comportamentos suspeitos
5. Recomendações de segurança

Código:
```
{codigo[:2000]}  # Limitar para não exceder contexto
```

Forneça análise técnica detalhada:
"""
        
        return gerar_codigo(prompt, max_tokens=1024)
    
    def _detectar_vulnerabilidades(self, codigo: str) -> List[str]:
        """Detecta vulnerabilidades comuns."""
        vulnerabilidades = []
        
        padroes_vuln = {
            'SQL Injection': [r'SELECT.*\+.*', r'INSERT.*\+.*', r'UPDATE.*\+.*'],
            'XSS': [r'innerHTML\s*=', r'document\.write\s*\(', r'eval\s*\('],
            'Buffer Overflow': [r'strcpy\s*\(', r'strcat\s*\(', r'gets\s*\('],
            'Command Injection': [r'system\s*\(.*\+', r'exec\s*\(.*\+', r'shell_exec'],
            'Path Traversal': [r'\.\./', r'\.\.\\\\', r'%2e%2e%2f'],
            'Hardcoded Secrets': [r'password\s*=\s*["\']', r'api_key\s*=\s*["\']']
        }
        
        for vuln, padroes in padroes_vuln.items():
            if any(re.search(padrao, codigo, re.IGNORECASE) for padrao in padroes):
                vulnerabilidades.append(vuln)
        
        return vulnerabilidades
    
    def _analisar_obfuscacao(self, codigo: str) -> Dict[str, Any]:
        """Analisa técnicas de ofuscação."""
        tecnicas = []
        
        if re.search(r'\\x[0-9a-fA-F]{2}', codigo):
            tecnicas.append('Hex encoding')
        
        if re.search(r'\\u[0-9a-fA-F]{4}', codigo):
            tecnicas.append('Unicode encoding')
        
        if re.search(r'eval\s*\(', codigo):
            tecnicas.append('Dynamic evaluation')
        
        if re.search(r'String\.fromCharCode', codigo):
            tecnicas.append('Character code conversion')
        
        # Calcular entropia (indicador de ofuscação)
        entropia = self._calcular_entropia(codigo)
        
        return {
            'tecnicas_detectadas': tecnicas,
            'entropia': entropia,
            'nivel_obfuscacao': 'ALTO' if entropia > 4.5 else 'MEDIO' if entropia > 3.5 else 'BAIXO'
        }
    
    def _calcular_entropia(self, texto: str) -> float:
        """Calcula entropia do texto (indicador de ofuscação)."""
        import math
        from collections import Counter
        
        if not texto:
            return 0
        
        contador = Counter(texto)
        total = len(texto)
        entropia = 0
        
        for freq in contador.values():
            p = freq / total
            entropia -= p * math.log2(p)
        
        return entropia
    
    def _analisar_comportamento(self, codigo: str) -> List[str]:
        """Analisa comportamentos do código."""
        comportamentos = []
        
        if re.search(r'network|socket|http|url', codigo, re.IGNORECASE):
            comportamentos.append('Comunicação de rede')
        
        if re.search(r'file|open|write|read', codigo, re.IGNORECASE):
            comportamentos.append('Manipulação de arquivos')
        
        if re.search(r'registry|regedit|hkey', codigo, re.IGNORECASE):
            comportamentos.append('Modificação do registro')
        
        if re.search(r'process|execute|shell|cmd', codigo, re.IGNORECASE):
            comportamentos.append('Execução de processos')
        
        return comportamentos
    
    def _calcular_nivel_risco(self, resultado: Dict) -> str:
        """Calcula nível de risco baseado na análise."""
        pontos_risco = 0
        
        # Padrões suspeitos
        pontos_risco += len(resultado.get('padroes_suspeitos', {})) * 2
        
        # Vulnerabilidades
        pontos_risco += len(resultado.get('vulnerabilidades', [])) * 3
        
        # Ofuscação
        if resultado.get('obfuscacao', {}).get('nivel_obfuscacao') == 'ALTO':
            pontos_risco += 5
        elif resultado.get('obfuscacao', {}).get('nivel_obfuscacao') == 'MEDIO':
            pontos_risco += 3
        
        if pontos_risco >= 10:
            return 'CRÍTICO'
        elif pontos_risco >= 6:
            return 'ALTO'
        elif pontos_risco >= 3:
            return 'MÉDIO'
        else:
            return 'BAIXO'

# Instância global
analisador = AnalisadorCodigoAvancado()

def analisar_codigo(codigo: str, linguagem: str = "auto") -> Dict[str, Any]:
    """Função de conveniência para análise completa."""
    return analisador.analisar_codigo_completo(codigo, linguagem)

def analisar_malware(codigo: str) -> Dict[str, Any]:
    """Função de conveniência para análise de malware."""
    return analisador.analisar_malware(codigo)

def engenharia_reversa_codigo(codigo: str) -> Dict[str, Any]:
    """Função de conveniência para engenharia reversa."""
    return analisador.engenharia_reversa_avancada(codigo)
