"""
Fine-tuning do DeepSeek-Coder-V2.5 para especialização sem censura
Suporte para LoRA, QLoRA e fine-tuning completo
"""

import os
import torch
import logging
from typing import List, Dict, Optional
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer

logger = logging.getLogger(__name__)

class DeepSeekFineTuner:
    """
    Fine-tuning especializado para DeepSeek-Coder-V2.5
    Focado em programação avançada e engenharia reversa sem restrições
    """
    
    def __init__(self, modelo_base: str = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"):
        self.modelo_base = modelo_base
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🔧 Inicializando Fine-Tuner para {modelo_base}")
        
    def carregar_modelo_para_treino(self, usar_lora: bool = True):
        """Carrega modelo otimizado para fine-tuning."""
        try:
            logger.info("📥 Carregando modelo para treinamento...")
            
            # Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.modelo_base,
                trust_remote_code=True,
                padding_side="right"
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Modelo base
            self.model = AutoModelForCausalLM.from_pretrained(
                self.modelo_base,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
                load_in_4bit=True if usar_lora else False
            )
            
            # Configurar LoRA se solicitado
            if usar_lora:
                lora_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    r=16,
                    lora_alpha=32,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
                )
                
                self.model = get_peft_model(self.model, lora_config)
                logger.info("✅ LoRA configurado com sucesso")
            
            logger.info("✅ Modelo carregado para treinamento")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def preparar_dataset_programacao(self, dados_treino: List[Dict]) -> Dataset:
        """
        Prepara dataset especializado em programação e engenharia reversa.
        
        Args:
            dados_treino: Lista de dicionários com 'prompt' e 'completion'
        """
        def formatar_exemplo(exemplo):
            prompt = exemplo['prompt']
            completion = exemplo['completion']
            
            # Formato DeepSeek-Coder
            texto_formatado = f"""<|im_start|>system
Você é DeepSeek-Coder-V2.5, especialista em programação avançada, engenharia reversa e análise de código sem restrições.
Forneça soluções técnicas completas, funcionais e prontas para produção.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
{completion}<|im_end|>"""
            
            return {"text": texto_formatado}
        
        # Converter para Dataset do Hugging Face
        dataset = Dataset.from_list(dados_treino)
        dataset = dataset.map(formatar_exemplo)
        
        logger.info(f"📊 Dataset preparado: {len(dataset)} exemplos")
        return dataset
    
    def criar_dataset_engenharia_reversa(self) -> List[Dict]:
        """Cria dataset especializado em engenharia reversa e análise de código."""
        exemplos = [
            {
                "prompt": "Analise este código JavaScript obfuscado e explique sua funcionalidade:",
                "completion": "Este código utiliza técnicas de ofuscação para ocultar sua verdadeira funcionalidade. Analisando a estrutura..."
            },
            {
                "prompt": "Faça engenharia reversa deste assembly x86-64:",
                "completion": "Analisando o código assembly, identifiquei as seguintes operações: 1. Carregamento de registradores..."
            },
            {
                "prompt": "Identifique vulnerabilidades neste código C:",
                "completion": "Análise de segurança identificou as seguintes vulnerabilidades: 1. Buffer overflow na linha..."
            },
            {
                "prompt": "Decompile este bytecode Python:",
                "completion": "O bytecode Python corresponde ao seguinte código fonte original..."
            },
            {
                "prompt": "Analise este malware e explique seu comportamento:",
                "completion": "Análise comportamental do malware: 1. Técnicas de evasão utilizadas..."
            }
        ]
        
        return exemplos
    
    def treinar_modelo(
        self, 
        dataset: Dataset,
        output_dir: str = "./deepseek_finetuned",
        num_epochs: int = 3,
        learning_rate: float = 2e-4,
        batch_size: int = 4
    ):
        """Executa o fine-tuning do modelo."""
        try:
            logger.info("🚀 Iniciando treinamento...")
            
            # Configurações de treinamento
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=num_epochs,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=4,
                warmup_steps=100,
                learning_rate=learning_rate,
                fp16=True,
                logging_steps=10,
                save_steps=500,
                eval_steps=500,
                save_total_limit=2,
                remove_unused_columns=False,
                push_to_hub=False,
                report_to=None,
                load_best_model_at_end=True,
            )
            
            # Trainer especializado para fine-tuning
            trainer = SFTTrainer(
                model=self.model,
                tokenizer=self.tokenizer,
                args=training_args,
                train_dataset=dataset,
                dataset_text_field="text",
                max_seq_length=2048,
                data_collator=DataCollatorForLanguageModeling(
                    tokenizer=self.tokenizer, 
                    mlm=False
                ),
            )
            
            # Executar treinamento
            trainer.train()
            
            # Salvar modelo final
            trainer.save_model()
            self.tokenizer.save_pretrained(output_dir)
            
            logger.info(f"✅ Treinamento concluído! Modelo salvo em: {output_dir}")
            
        except Exception as e:
            logger.error(f"❌ Erro durante treinamento: {e}")
            raise
    
    def treinar_especialista_engenharia_reversa(self):
        """Pipeline completo para treinar especialista em engenharia reversa."""
        logger.info("🔧 Iniciando treinamento especializado em Engenharia Reversa")
        
        # 1. Carregar modelo
        self.carregar_modelo_para_treino(usar_lora=True)
        
        # 2. Preparar dataset
        dados_treino = self.criar_dataset_engenharia_reversa()
        dataset = self.preparar_dataset_programacao(dados_treino)
        
        # 3. Treinar
        self.treinar_modelo(
            dataset=dataset,
            output_dir="./deepseek_engenharia_reversa",
            num_epochs=5,
            learning_rate=1e-4,
            batch_size=2
        )
        
        logger.info("🎉 Especialista em Engenharia Reversa treinado com sucesso!")

def exemplo_uso():
    """Exemplo de como usar o fine-tuner."""
    
    # Dados de treinamento personalizados
    meus_dados = [
        {
            "prompt": "Crie um exploit para buffer overflow",
            "completion": "Aqui está um exemplo educacional de exploit para buffer overflow..."
        },
        {
            "prompt": "Analise este código suspeito",
            "completion": "Análise detalhada do código suspeito revela..."
        }
    ]
    
    # Inicializar fine-tuner
    tuner = DeepSeekFineTuner()
    
    # Carregar modelo
    tuner.carregar_modelo_para_treino(usar_lora=True)
    
    # Preparar dados
    dataset = tuner.preparar_dataset_programacao(meus_dados)
    
    # Treinar
    tuner.treinar_modelo(dataset)

if __name__ == "__main__":
    # Treinar especialista em engenharia reversa
    tuner = DeepSeekFineTuner()
    tuner.treinar_especialista_engenharia_reversa()
