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
        MatInputModule, MatProgressSpinnerModule,
        MatTreeModule, MatCardModule, MatTabsModule, MatSnackBarModule } from  '@angular/material';
        import { FormsModule, ReactiveFormsModule } from '@angular/forms';
        import { GoogleChartsModule } from 'angular-google-charts';
import {DragDropModule} from '@angular/cdk/drag-drop';
import { FileService } from 'src/app/service/file.service';
import { MediaPlayerService } from './service/media-player.service';
import { UserService } from 'src/app/service/user.service';
import { ClipboardModule } from 'ngx-clipboard';

import { FileListComponent } from './folder-view/file-list/file-list.component';
import { MusicPlayerComponent } from './folder-view/file-list/music-player/music-player.component';
import { HttpClientModule, HttpClientXsrfModule } from '@angular/common/http';
import { FolderViewComponent } from './folder-view/folder-view.component';
import { FolderTasksComponent } from './folder-view/folder-tasks/folder-tasks.component';
import { VideoPlayerComponent } from './folder-view/file-list/video-player/video-player.component';
import { PictureViewerComponent } from './folder-view/file-list/picture-viewer/picture-viewer.component';
import { CodeViewerComponent } from './folder-view/file-list/code-viewer/code-viewer.component';
import { HighlightModule, HIGHLIGHT_OPTIONS  } from 'ngx-highlightjs';
import { DialogCreateNewFolderComponent } from './folder-view/folder-tasks/dialog-create-new-folder/dialog-create-new-folder.component';
import { DialogNewFileUploadComponent } from './folder-view/folder-tasks/dialog-new-file-upload/dialog-new-file-upload.component';
import { DialogNewURLDownloadComponent } from './folder-view/folder-tasks/dialog-new-url-download/dialog-new-url-download.component';
import { SystemComponent } from './system/system.component';
import { NetworkUsageComponent } from './system/network-usage/network-usage.component';
import { SystemFactsComponent } from './system/system-facts/system-facts.component';
import { FileTasksComponent } from './folder-view/file-tasks/file-tasks.component';
import { ConfirmDeleteDialogComponent } from './folder-view/file-tasks/confirm-delete-dialog/confirm-delete-dialog.component';
import { RenameDialogComponent } from './folder-view/file-tasks/rename-dialog/rename-dialog.component';
import { MoveFileDialogComponent } from './folder-view/file-tasks/move-file-dialog/move-file-dialog.component';
import { DialogNewMagnetDownloadComponent } from './folder-view/folder-tasks/dialog-new-magnet-download/dialog-new-magnet-download.component';
import { DialogNewTorrentDownloadComponent } from './folder-view/folder-tasks/dialog-new-torrent-download/dialog-new-torrent-download.component';
import { RootComponent } from './root/root.component';
import { LoginComponent } from './login/login.component';
import { NavBarComponent } from './nav-bar/nav-bar.component';
import { MediaPlayerComponent } from './media-player/media-player.component';
import { DialogNewPlaylistComponent } from './media-player/dialog-new-playlist/dialog-new-playlist.component';

import { DialogAddMediaComponent } from './media-player/dialog-add-media/dialog-add-media.component';
import { ConfirmDeletePlaylistComponent } from './media-player/confirm-delete-playlist/confirm-delete-playlist.component';
import { UserAccountsComponent } from './system/user-accounts/user-accounts.component';
import { DeleteComponent } from './system/user-accounts/delete/delete.component';
import { EditComponent } from './system/user-accounts/edit/edit.component';

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
    DialogNewURLDownloadComponent,
    SystemComponent,
    NetworkUsageComponent,
    SystemFactsComponent,
    FileTasksComponent,
    ConfirmDeleteDialogComponent,
    RenameDialogComponent,
    MoveFileDialogComponent,
    DialogNewMagnetDownloadComponent,
    DialogNewTorrentDownloadComponent,
    RootComponent,
    LoginComponent,
    NavBarComponent,
    MediaPlayerComponent,
    DialogNewPlaylistComponent,
    DialogAddMediaComponent,
    ConfirmDeletePlaylistComponent,
    UserAccountsComponent,
    DeleteComponent,
    EditComponent,
  ],
  entryComponents: [
    MusicPlayerComponent,
    VideoPlayerComponent,
    CodeViewerComponent,
    PictureViewerComponent,
    DialogCreateNewFolderComponent,
    DialogNewFileUploadComponent,
    DialogNewURLDownloadComponent,
    ConfirmDeleteDialogComponent,
    RenameDialogComponent,
    MoveFileDialogComponent,
    DialogAddMediaComponent,
    ConfirmDeletePlaylistComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    ClipboardModule,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' }),
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
    MatCardModule,
    GoogleChartsModule,
    MatTreeModule,
    DragDropModule,
    MatTabsModule,
    MatSnackBarModule,
  ],
  providers: [
    {
      provide: HIGHLIGHT_OPTIONS,
      useValue: {
        languages: getHighlightLanguages()
      }
    },
    FileService,
    MediaPlayerService,
    UserService,
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule { }
