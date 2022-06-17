FROM python:3.9
WORKDIR /code
COPY   ./ /code/
RUN apt-get update
#RUN apt-get install -y iputils-ping
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
ENV MONGO_URL=mongodb+srv://zaragoza:zaragoza@cluster0.xejuy.mongodb.net/library?retryWrites=true&w=majority
ENV KAFKA_URL=kafka:9092
CMD ["uvicorn","main:app", "--host","0.0.0.0", "--port", "8000"]