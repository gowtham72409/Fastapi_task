import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline
from langchain.chains.retrieval_qa.base import RetrievalQA
from sentence_transformers import SentenceTransformer

class RAGService:

    def __init__(self):
        self.vector_path="vector_db"

        self.embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        generator=pipeline("text-generation",model="distilgpt2",max_new_tokens=200)

        self.llm=HuggingFacePipeline(pipeline=generator)

        self.vector_store=None
        self.qa_chain=None

    def index_book(self,pdf_path):
        loader=PyPDFLoader(pdf_path)

        document=loader.load()

        splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=200)

        doc=splitter.split_documents(document)

        self.vector_store=FAISS.from_documents(doc,self.embedding)

        self.vector_store.save_local(self.vector_path)

        retriever=self.vector_store.as_retriever(search_kwargs={"k":3})

        self.qa_chain=RetrievalQA.from_chain_type(llm=self.llm,retriever=retriever,
                                                  return_source_documents=True)
        
        return {"message":"Book Indexed Successfully","chunks_create":len(doc)}
        
    def load_vector_store(self):

        if os.path.exists("vector_db/index.faiss"):
            self.vector_store = FAISS.load_local(
            self.vector_path,
            self.embedding,
            allow_dangerous_deserialization=True
        )
        else:
            print("Creating new vector DB")
            self.vector_store = None
            
    def ask_question(self,question):

        if self.qa_chain is None:
            return {"error":"No book indexed"}
        
        result=self.qa_chain.invoke({"query":question})
        pages=[]

        for doc in result["source_documents"]:
            pages.append(doc.metadata["page"]+1)

        return {"question": question,"answer": result["result"],"source_pages": pages}