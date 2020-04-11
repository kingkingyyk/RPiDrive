from django.http import JsonResponse
from . import requires_admin
import psutil, humanize, sys, platform, time

def natural_bandwidth(value):
    if value < 1024:
        return '{} B/s'.format(value)
    else:
        return humanize.naturalsize(value) + '/s'

def retrieve_system_info(cpu=True, memory=True, sensors=True, env=True, network=True):
    system_data = {}

    if cpu:
        cpu_cores = psutil.cpu_count() if psutil.cpu_count(False) is None else psutil.cpu_count(False)
        cpu_threads = psutil.cpu_count(True)

        system_data['CPU'] = [
            {'title': 'Cores', 'value': '{} cores, {} threads'.format(cpu_cores, cpu_threads)},
            {'title': 'Clock', 'value': ', '.join([str(x.current)+' MHz' for x in psutil.cpu_freq(percpu=True)])},
            {'title': 'Usage', 'value': '{}%'.format(psutil.cpu_percent())},
        ]

    if memory:
        memory = psutil.virtual_memory()
        system_data['Memory'] = [
            {'title': 'Total', 'value': humanize.naturalsize(memory.total)},
            {'title': 'Used',  'value': humanize.naturalsize(memory.used)},
            {'title': 'Free', 'value': humanize.naturalsize(memory.available)},
        ]

    if sensors and 'sensors_temperatures' in psutil.__dict__:
        system_data['Sensors'] = [{'title': 'CPU Temperature', 'value': '{}°C'.format(psutil.sensors_temperatures(False)['cpu-thermal'][0].current)}]

    if env:
        system_data['Environment'] = [
            {'title': 'OS', 'value' : '{} {}'.format(platform.system(), platform.release())},
            {'title': 'Python Version', 'value': sys.version},
        ]

    if network:
        network_before = psutil.net_io_counters()
        time.sleep(0.5)
        network_after = psutil.net_io_counters()

        download_speed = ((network_after.bytes_recv - network_before.bytes_recv)*2)
        upload_speed = ((network_after.bytes_sent - network_before.bytes_sent)*2)

        total_downloads = network_after.bytes_recv/(1024*1024)
        total_uploads = network_after.bytes_sent/(1024*1024)

        network_data = {'upload-speed': download_speed/1024,
                        'download-speed': upload_speed/1024,
                        'upload-speed-natural': natural_bandwidth(upload_speed),
                        'download-speed-natural': natural_bandwidth(download_speed),
                        'total-downloads': total_downloads,
                        'total-uploads': total_uploads,
                        }

    all_data = {}
    if cpu or memory or sensors or env:
        all_data['system_data'] = system_data

    if network:
        all_data['network_data'] = network_data

    return all_data

@requires_admin
def get_facts(request):
    return JsonResponse(retrieve_system_info(network=False))

@requires_admin
def get_network_facts(request):
    return JsonResponse(retrieve_system_info(cpu=False, memory=False, sensors=False, env=False))