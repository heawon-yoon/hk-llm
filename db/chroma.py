import os
import sys

from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from langchain_chroma import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, CSVLoader, UnstructuredFileLoader, PyPDFLoader
from config import conf

class ChromaLoader(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__init_once__()
        return cls._instance

    def __init_once__(self):
        self.use_rag = False
        self.load_data()

        self.template = """
                        优先根据下面内容回答问题
                        {context}
                        
                        这个是用户问题,上面没有内容就自由发挥
                        {question}
                        """




    def load_data(self):
        dir = conf().get("rag_path")
        if dir is None:
            dir = "./data/"
        for filename in os.listdir(dir):
            self.load_embeddings()
            if filename.endswith(".csv"):
                self.use_rag = True
                csv_loader = CSVLoader(dir+filename)
                csv_documents = csv_loader.load()
                self.db = Chroma.from_documents(csv_documents, self.embeddings)

            elif filename.endswith(".docx"):
                self.use_rag = True
                doc_loader = Docx2txtLoader(dir+filename)
                doc_documents = doc_loader.load()
                text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=0)
                docs = text_splitter.split_documents(doc_documents)
                self.db = Chroma.from_documents(docs, self.embeddings)
            elif filename.endswith(".pdf"):
                self.use_rag = True
                pdf_loader = PyPDFLoader(dir + filename)
                pdf_documents = pdf_loader.load()
                text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=0)
                docs = text_splitter.split_documents(pdf_documents)
                self.db = Chroma.from_documents(docs, self.embeddings)
            elif filename.endswith(".txt"):
                self.use_rag = True
                txt_loader = UnstructuredFileLoader(dir + filename)
                txt_documents = txt_loader.load()
                text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=0)
                docs = text_splitter.split_documents(txt_documents)
                self.db = Chroma.from_documents(docs, self.embeddings)

    def load_embeddings(self):
        model_name = "BAAI/bge-large-zh-v1.5"
        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
        )


    def rag_prompt(self,query):

        if self.use_rag:
            retriever = self.db.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 2, "score_threshold": 0.1},
            )
            context = retriever.invoke(query)
            if context:
                query = self.template.format(context=context[0].page_content, question=query)
        return query



if __name__ == '__main__':
    # 获取当前文件的绝对路径
    file_path = os.path.abspath(__file__)

    # 获取当前文件的根目录路径
    root_path = os.path.dirname(file_path)
    parent_directory_path = os.path.dirname(root_path)

    sys.path.append(parent_directory_path)
    db = ChromaLoader("银杆眼部细节刷")
    print(db.query)

