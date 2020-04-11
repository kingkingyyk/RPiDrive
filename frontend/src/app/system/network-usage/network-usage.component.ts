import { Component, HostListener, OnInit } from '@angular/core';
import { FileService } from 'src/app/service/file.service'
import { timer } from 'rxjs';

@Component({
  selector: 'app-network-usage',
  templateUrl: './network-usage.component.html',
  styleUrls: ['./network-usage.component.css']
})
export class NetworkUsageComponent implements OnInit {
  uploadSpeedText : string;
  downloadSpeedText : string;
  totalUploads : string;
  totalDownloads : string;
  currUpload: number;
  currDownload: number;
  loaded : boolean;

  chartTitle = 'Bandwidth';
  type = 'LineChart';
  data = [];
  columnNames = ["Time", "Download", "Upload"];
  options = {   
     hAxis: {
        title: 'Timestamp',
        titleTextStyle: {
          color: 'white',
          fontName: 'Roboto',
        },
        textStyle: {
          color: 'white',
          fontName: 'Roboto',
        },
        gridlines: {
          color: 'transparent'
        },
        format: 'hh:mm:s a'
     },
     vAxis:{
        title: 'Bandwidth\n(KB/s)',
        titleTextStyle: {
          color: 'white',
          fontName: 'Roboto',
        },
        textStyle: {
          color: 'white',
          fontName: 'Roboto',
        },
        gridlines: {
          color: 'transparent'
        },
     },
     legend: {
        textStyle: {
          color: 'white',
          fontName: 'Roboto',
        } 
     },
     chartArea: {
       width: '70%'
     },
     backgroundColor: "transparent",
      pointSize:5
  };
  width = 1000;
  height = "auto";

  timer: any;

  constructor(private fileService: FileService) {}

  ngOnInit() {
    this.timer = timer(0, 2000).subscribe(() => {
      this.loadData();
    })
  }

  ngOnDestroy() {
    if (this.timer) this.timer.unsubscribe();
  }

  convertTotalUsage(value: number) {
    let units = ['MB', 'GB', 'TB', 'PB'];
    let idx = 0;
    while (value>1024) {
      value/=1024;
      idx += 1;
    }
    return value.toFixed(1)+" "+units[idx];
  }

  loadData() {
    this.fileService.getNetworkFacts().subscribe((data:  object) => this.setData(data));
  }

  setData(data: object) {
    this.loaded = true;
    this.uploadSpeedText = data['network_data']['upload-speed-natural'];
    this.downloadSpeedText = data['network_data']['download-speed-natural'];
    this.totalUploads = this.convertTotalUsage(data['network_data']['total-uploads']);
    this.totalDownloads = this.convertTotalUsage(data['network_data']['total-downloads']);

    const cloned = Object.assign([], this.data);
    cloned.push([new Date(), data['network_data']['upload-speed'], data['network_data']['download-speed']]);
    while (cloned.length>60) cloned.shift();
    this.data = cloned;
    this.resizeChart();
  }

  @HostListener('window:resize', ['$event'])
  onWindowReize(event: any) {
    this.resizeChart();
  }

  resizeChart() {
    this.width = Math.max(document.documentElement.clientWidth, window.innerWidth || 0) - 240;
    if (this.width < 500) this.options.chartArea.width = "50%";
    else if (this.width < 1200) this.options.chartArea.width = "60%";
    else this.options.chartArea.width = "70%";
  }
}
