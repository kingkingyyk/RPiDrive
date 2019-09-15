from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from ..models import *
from ..enum import *
import psutil, humanize, time, json, platform, sys


@login_required
def manage_storage(request):
    drive = Drive.objects.get()
    storages = Storage.objects.all()

    context = {'drive': drive,
               'storages': storages,
               'weekdays': weekdays,
               'storage_sync_period': storage_sync_period,
               }

    return render(request, 'drive/manage-storage.html', context)


@login_required
def system_status(request):
    drive = Drive.objects.get()

    cpu_data = [
        ('Cores', '{} cores, {} threads'.format(psutil.cpu_count(False), psutil.cpu_count(True))),
        ('Clock', ', '.join([str(x.current)+'MHz' for x in psutil.cpu_freq(percpu=True)])),
        ('Usage', '{}%'.format(psutil.cpu_percent())),
    ]

    memory = psutil.virtual_memory()
    memory_data = [
        ('Total', humanize.naturalsize(memory.total)),
        ('Used',  humanize.naturalsize(memory.used)),
        ('Free', humanize.naturalsize(memory.available)),
    ]

    sensor_data = []
    if 'sensors_temperatures' in psutil.__dict__:
        sensor_data = [('CPU Temperature', '{}°C'.format(psutil.sensors_temperatures(False)['cpu-thermal'][0].current))]

    env_data = [
        ('OS', '{} {}'.format(platform.system(), platform.release())),
        ('Python Version', sys.version)
    ]

    data = {'CPU': cpu_data,
            'Memory': memory_data,
            'Sensors': sensor_data,
            'Environment': env_data}

    context = { 'drive': drive,
                'data': data,
               }

    return render(request, 'drive/system-status.html', context)


@login_required
def network_status(request):
    network_before = psutil.net_io_counters()
    time.sleep(0.5)
    network_after = psutil.net_io_counters()

    download_speed = ((network_after.bytes_recv - network_before.bytes_recv)*2)
    upload_speed = ((network_after.bytes_sent - network_before.bytes_sent)*2)

    network_data = {'upload-speed': download_speed*8/1024,
                    'download-speed': upload_speed*8/1024,
                    'upload-speed-natural': natural_bandwidth(upload_speed),
                    'download-speed-natural': natural_bandwidth(download_speed),
                    }
    return HttpResponse(json.dumps(network_data), content_type='application/json')


def natural_bandwidth(value):
    if value < 1024:
        return '{} bps'.format(value)
    else:
        v, unit = humanize.naturalsize(value).split(' ')
        unit = unit[0] + unit.lower()[1:]
        return '{} {}ps'.format(v, unit)