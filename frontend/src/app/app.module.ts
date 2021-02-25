import { MomentModule } from 'ngx-moment';

import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent, CheckLoginComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HttpClientModule, HttpClientXsrfModule } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';

import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatBadgeModule } from '@angular/material/badge';
import { MatBottomSheetModule } from '@angular/material/bottom-sheet';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';
import { MatRippleModule } from '@angular/material/core';
import { MatSelectModule } from '@angular/material/select';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSliderModule } from '@angular/material/slider';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatStepperModule } from '@angular/material/stepper';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ClipboardModule } from '@angular/cdk/clipboard';
import { DragDropModule } from '@angular/cdk/drag-drop';

import { NgxFilesizeModule } from 'ngx-filesize';
import { HighlightJsModule } from 'ngx-highlight-js';

import { LoginComponent } from './drive/login/login.component';
import { SetupComponent } from './drive/setup/setup.component';
import { MainComponent } from './drive/main/main.component';
import { FolderComponent, 
        StorageProviderTableComponent,
        SearchTableComponent,
        DialogEditStorageProviderComponent,
        DialogDeleteStorageProviderComponent,
        FolderTableComponent, 
        DialogCreateFolderComponent,
        DialogFilePreviewComponent,
        DialogDeleteFileComponent,
        DialogRenameFileComponent,
        DialogShareFileComponent,
        DialogMoveFileComponent,
        DialogFileUploadComponent,
        DialogFolderUploadComponent } from './drive/folder/folder.component';
import { MediaPlayerComponent,
         DialogCreatePlaylistComponent,
         PlaylistComponent,
         DialogDeletePlaylistComponent,
         PlaylistFileBrowserComponent,
         PlaylistAddFileService } from './drive/media-player/media-player.component';
import { SettingsComponent,
        UserSettingsComponent,
        NetworkSettingsComponent,
        SystemSettingsComponent, 
        EditUserComponent,
        DeleteUserComponent} from './drive/settings/settings.component';

@NgModule({
  declarations: [
    AppComponent,
    CheckLoginComponent,
    LoginComponent,
    SetupComponent,
    MainComponent,
    FolderComponent,
    StorageProviderTableComponent,
    SearchTableComponent,
    DialogEditStorageProviderComponent,
    DialogDeleteStorageProviderComponent,
    FolderTableComponent,
    DialogCreateFolderComponent,
    DialogFilePreviewComponent,
    DialogDeleteFileComponent,
    DialogRenameFileComponent,
    DialogShareFileComponent,
    DialogMoveFileComponent,
    DialogFileUploadComponent,
    DialogFolderUploadComponent,
    MediaPlayerComponent,
    DialogCreatePlaylistComponent,
    PlaylistComponent,
    DialogDeletePlaylistComponent,
    PlaylistFileBrowserComponent,
    SettingsComponent,
    UserSettingsComponent,
    EditUserComponent,
    DeleteUserComponent,
    NetworkSettingsComponent,
    SystemSettingsComponent
  ],
  imports: [
    MomentModule,
    BrowserModule,
    FormsModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' }),
    ReactiveFormsModule,
    MatAutocompleteModule,
    MatBadgeModule,
    MatBottomSheetModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatDialogModule,
    MatDividerModule,
    MatExpansionModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatMenuModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatRadioModule,
    MatRippleModule,
    MatSelectModule,
    MatSidenavModule,
    MatSlideToggleModule,
    MatSliderModule,
    MatSnackBarModule,
    MatSortModule,
    MatStepperModule,
    MatTableModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    ClipboardModule,
    DragDropModule,
    NgxFilesizeModule,
    HighlightJsModule,
  ],
  providers: [PlaylistAddFileService],
  bootstrap: [AppComponent]
})
export class AppModule { }
