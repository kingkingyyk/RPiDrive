import { BrowserModule, Title } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatToolbarModule, MatIconModule, MatSidenavModule, 
        MatListModule, MatButtonModule, MatSortModule, MatTableModule, 
        MatCheckboxModule, MatSelectModule, MatMenuModule, 
        MatProgressBarModule, MatTooltipModule, MatRippleModule,
        MatDialogModule, MatExpansionModule, MatFormFieldModule,
        MatInputModule, MatProgressSpinnerModule } from  '@angular/material';
  
import { FileService } from 'src/app/service/file.service';
import { ClipboardModule } from 'ngx-clipboard';

import { FileListComponent } from './folder-view/file-list/file-list.component';
import { MusicPlayerComponent } from './folder-view/file-list/music-player/music-player.component';
import { HttpClientModule } from '@angular/common/http';
import { FolderViewComponent } from './folder-view/folder-view.component';
import { FolderTasksComponent } from './folder-view/folder-tasks/folder-tasks.component';
import { VideoPlayerComponent } from './folder-view/file-list/video-player/video-player.component';
import { PictureViewerComponent } from './folder-view/file-list/picture-viewer/picture-viewer.component';
import { CodeViewerComponent } from './folder-view/file-list/code-viewer/code-viewer.component';
import { HighlightModule, HIGHLIGHT_OPTIONS  } from 'ngx-highlightjs';
import { DialogCreateNewFolderComponent } from './folder-view/folder-tasks/dialog-create-new-folder/dialog-create-new-folder.component';
import { DialogNewFileUploadComponent } from './folder-view/folder-tasks/dialog-new-file-upload/dialog-new-file-upload.component';
import { DialogAddNewDownloadComponent } from './folder-view/folder-tasks/dialog-add-new-download/dialog-add-new-download.component';
import { SystemComponent } from './system/system.component';
import { NetworkUsageComponent } from './system/network-usage/network-usage.component';
import { SystemFactsComponent } from './system/system-facts/system-facts.component';
import { FileTasksComponent } from './folder-view/file-tasks/file-tasks.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFileUploadModule } from 'angular-material-fileupload';
import { GoogleChartsModule } from 'angular-google-charts';
import { ConfirmDeleteDialogComponent } from './folder-view/file-tasks/confirm-delete-dialog/confirm-delete-dialog.component';
import { RenameDialogComponent } from './folder-view/file-tasks/rename-dialog/rename-dialog.component';

export function getHighlightLanguages() {
  return {
    typescript: () => import('highlight.js/lib/languages/typescript'),
    css: () => import('highlight.js/lib/languages/css'),
    xml: () => import('highlight.js/lib/languages/xml'),
    python: () => import('highlight.js/lib/languages/python'),
    java: () => import('highlight.js/lib/languages/java'),
    cpp: () => import('highlight.js/lib/languages/cpp'),
  };
}

@NgModule({
  declarations: [
    AppComponent,
    FileListComponent,
    FolderViewComponent,
    FolderTasksComponent,
    MusicPlayerComponent,
    VideoPlayerComponent,
    PictureViewerComponent,
    CodeViewerComponent,
    DialogCreateNewFolderComponent,
    DialogNewFileUploadComponent,
    DialogAddNewDownloadComponent,
    SystemComponent,
    NetworkUsageComponent,
    SystemFactsComponent,
    FileTasksComponent,
    ConfirmDeleteDialogComponent,
    RenameDialogComponent,
  ],
  entryComponents: [
    MusicPlayerComponent,
    VideoPlayerComponent,
    CodeViewerComponent,
    PictureViewerComponent,
    DialogCreateNewFolderComponent,
    DialogNewFileUploadComponent,
    DialogAddNewDownloadComponent,
    ConfirmDeleteDialogComponent,
    RenameDialogComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    ClipboardModule,
    HttpClientModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatCheckboxModule,
    MatSelectModule,
    MatSortModule,
    MatMenuModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatRippleModule,
    MatDialogModule,
    HighlightModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    FormsModule,
    ReactiveFormsModule,
    MatFileUploadModule,
    GoogleChartsModule,
  ],
  providers: [
    {
      provide: HIGHLIGHT_OPTIONS,
      useValue: {
        languages: getHighlightLanguages()
      }
    },
    FileService
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
