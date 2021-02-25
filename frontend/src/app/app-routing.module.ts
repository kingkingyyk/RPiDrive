import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { Url as DriveUrl } from 'src/app/drive/urls';
import { LoginComponent } from 'src/app/drive/login/login.component';
import { SetupComponent } from 'src/app/drive/setup/setup.component';
import { MainComponent } from 'src/app/drive/main/main.component';
import { FolderComponent } from './drive/folder/folder.component';
import { MediaPlayerComponent } from './drive/media-player/media-player.component';
import { SettingsComponent } from './drive/settings/settings.component';

const routes: Routes = [
    { path: DriveUrl.getRootURL(), component: MainComponent },
    { path: DriveUrl.getLoginAbsURL(), component: LoginComponent},
    { path: DriveUrl.getSetupAbsURL(), component: SetupComponent},
    { path: DriveUrl.getFolderAbsURL(), component: FolderComponent,
      children: [
        {path: ':folderid', component: FolderComponent, pathMatch: 'full'}
      ]
    },
    { path: DriveUrl.getMediaPlayerAbsUrl(), component: MediaPlayerComponent,
      children: [
        {path: 'playlists/:playlistid', component: MediaPlayerComponent, pathMatch: 'full'},
      ]},
    { path: DriveUrl.getSettingsAbsUrl(), component: SettingsComponent,
      children: [
        {path: ':type', component: SettingsComponent, pathMatch: 'full'},
      ]
    },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
