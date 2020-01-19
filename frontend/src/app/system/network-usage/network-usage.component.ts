import { Component, OnInit } from '@angular/core';
import { FileService } from 'src/app/service/file.service'
import { interval } from 'rxjs';
import { flatMap } from 'rxjs/operators'

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
  loaded : boolean;

  constructor(private fileService: FileService) {}

  ngOnInit() {
    this.fileService.getNetworkFacts().subscribe((data:  object) => this.setData(data));

    interval(2000)
    .pipe(
        flatMap(() => this.fileService.getNetworkFacts())
    )
    .subscribe((data:  object) => this.setData(data));
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

  setData(data: object) {
    this.loaded = true;
    this.uploadSpeedText = data['network_data']['upload-speed-natural'];
    this.downloadSpeedText = data['network_data']['download-speed-natural'];
    this.totalUploads = this.convertTotalUsage(data['network_data']['total-uploads']);
    this.totalDownloads = this.convertTotalUsage(data['network_data']['total-downloads']);
  }
}
