from transformers import pipeline

pipeline('sentiment-analysis', device=-1)
