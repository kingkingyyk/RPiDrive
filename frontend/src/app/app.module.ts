import { BrowserModule, Title } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatToolbarModule, MatIconModule, MatSidenavModule, 
        MatListModule, MatButtonModule, MatSortModule, MatTableModule, 
        MatCheckboxModule, MatSelectModule, MatMenuModule, 
        MatProgressBarModule, MatTooltipModule, MatRippleModule,
        MatDialogModule, MatExpansionModule } from  '@angular/material';
import { FileListComponent } from './file-list/file-list.component';
import { MusicPlayerComponent } from './file-list/music-player/music-player.component';
import { HttpClientModule } from '@angular/common/http';
import { FolderViewComponent } from './folder-view/folder-view.component';
import { FolderTasksComponent } from './folder-tasks/folder-tasks.component';
import { VideoPlayerComponent } from './file-list/video-player/video-player.component';
import { PictureViewerComponent } from './file-list/picture-viewer/picture-viewer.component';
import { CodeViewerComponent } from './file-list/code-viewer/code-viewer.component';
import { HighlightModule, HIGHLIGHT_OPTIONS  } from 'ngx-highlightjs';
import { DialogCreateNewFolderComponent } from './file-list/dialog-create-new-folder/dialog-create-new-folder.component';

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
  ],
  entryComponents: [
    MusicPlayerComponent,
    VideoPlayerComponent,
    CodeViewerComponent,
    PictureViewerComponent,
    DialogCreateNewFolderComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
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
  ],
  providers: [
    {
      provide: HIGHLIGHT_OPTIONS,
      useValue: {
        languages: getHighlightLanguages()
      }
    }
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
