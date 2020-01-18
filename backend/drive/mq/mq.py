from django.conf import settings
from datetime import timedelta, datetime
from threading import Thread
import pika, random, uuid, time, json

class MQChannels:
    FOLDER_TO_CREATE = "operation.folder.create"
    FOLDER_CREATED = "operation.folder.created"
    FOLDER_RENAMED = "operation.folder.renamed"
    FOLDER_MOVED = "operation.folder.moved"
    FOLDER_DELETED = "operation.folder.deleted"

    FILE_CREATED = "operation.file.created"
    FILE_RENAMED = "operation.file.renamed"
    FILE_MOVED = "operation.file.moved"
    FILDER_DELETED = "operation.file.deleted"

    DOWNLOAD_ADDED = "download.added"
    DOWNLOAD_DELETED = "download.deleted"

    RESPONSE_QUEUE = "response.{}"

class MQUtils:

    @staticmethod
    def _create_conn_params():
        conn_params = []
        for conn_settings in settings.MESSAGE_QUEUE:
            conn_params.append(pika.ConnectionParameters(
                credentials=pika.PlainCredentials(conn_settings['USER'], conn_settings['PASSWORD']),
                host=conn_settings['HOST'],
                port=conn_settings['PORT'],
            ))
        random.shuffle(conn_params)
        return conn_params

    @staticmethod
    def subscribe_channel(channel_name, callback):
        def loop(channel_name, callback):
            while True:
                try:
                    connection = pika.BlockingConnection(MQUtils._create_conn_params())
                    channel = connection.channel()
                    channel.queue_declare(channel_name, durable=False, auto_delete=True)
                    channel.basic_consume(channel_name, callback)
                    try:
                        channel.start_consuming()
                    except KeyboardInterrupt:
                        channel.stop_consuming()
                        connection.close()
                        break
                except pika.exceptions.ConnectionClosedByBroker:
                    continue
                except pika.exceptions.AMQPChannelError:
                    break
                except pika.exceptions.AMQPConnectionError:
                    continue
                time.sleep(0.5)
        Thread(target=loop, args=(channel_name, callback)).start()

    @staticmethod
    def push_to_channel(channel_name, message, expect_response, timeout=5.0):
        if expect_response:
            response_queue = MQChannels.RESPONSE_QUEUE.format(uuid.uuid4())

        conn = pika.BlockingConnection(MQUtils._create_conn_params())
        channel = conn.channel()
        channel.queue_declare(channel_name, durable=False, auto_delete=True)
        if expect_response:
            channel.queue_declare(response_queue, durable=False, auto_delete=True)
            channel.basic_publish('', channel_name, json.dumps({'reply-queue': response_queue, 'message': message}))
        else:
            channel.basic_publish('', channel_name, json.dumps({'message': message}))
        if expect_response:
            start_time = datetime.now()
            max_time = timedelta(seconds=timeout)
            flag = False
            while datetime.now() - start_time < max_time:
                method_frame, header_frame, body = channel.basic_get(queue=response_queue)
                if method_frame:
                    channel.basic_ack(method_frame.delivery_tag)
                    flag = True
                else:
                    time.sleep(0.1)

        channel.close()
        conn.close()

        if expect_response:
            if not flag:
                raise TimeoutError()
            else:
                return json.loads(body)