import { AfterViewInit, Component, Input, OnInit, SimpleChanges, ViewChild } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Title } from '@angular/platform-browser';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';
import { GetStorageProvidersResponse, StorageProvider, StorageProviderType } from '../models';

@Component({
  selector: 'app-folder',
  templateUrl: './folder.component.html',
  styleUrls: ['./folder.component.scss']
})
export class FolderComponent implements OnInit {
  storageProviders: StorageProvider[] = [];
  loadingCount: number = 0;
  folderId: string = '';

  constructor(private service: CommonService,
              private router: Router,
              private route: ActivatedRoute,
              private titleService: Title) {
                this.titleService.setTitle('File Explorer - RPi Drive');
              }

  ngOnInit(): void {
    this.loadStorageProviders();
    this.checkAndLoadFolder();
    this.router.events.subscribe((value) => this.checkAndLoadFolder());
  }

  loadStorageProviders(): void {
    this.loadingCount += 1;
    this.service.getStorageProviders().subscribe((data : GetStorageProvidersResponse) => {
      this.storageProviders = data.values;
    }).add(() => {
      this.loadingCount -= 1;
    });
  }

  checkAndLoadFolder(): void {
    this.folderId = this.route.firstChild?.snapshot.params['folderid'];
  }
}

@Component({
  selector: 'app-storage-provider-table',
  templateUrl: './storage-provider-table.component.html',
  styleUrls: ['./storage-provider-table.component.scss']
})
export class StorageProviderTableComponent implements AfterViewInit {
  @Input() storageProviders: StorageProvider[];
  displayedColumns: string[] = ['name', 'path', 'usedSpace', 'totalSpace'];
  dataSource: MatTableDataSource<StorageProvider>;

  @ViewChild(MatSort) sort: MatSort;

  constructor(private router: Router,
              private route: ActivatedRoute) {
    this.dataSource = new MatTableDataSource(this.storageProviders);
  }

  ngOnChanges(changes: SimpleChanges) {
    this.dataSource.data = this.storageProviders;
  }

  ngAfterViewInit() {
    this.dataSource.sort = this.sort; 
  }

  loadStorageProviderFolder(storageProvider : StorageProvider) {
    this.router.navigate([storageProvider.rootFolder], { relativeTo: this.route });
  }
}

@Component({
  selector: 'app-folder-table',
  templateUrl: './folder-table.component.html',
  styleUrls: ['./folder-table.component.scss']
})
export class FolderTableComponent {

}