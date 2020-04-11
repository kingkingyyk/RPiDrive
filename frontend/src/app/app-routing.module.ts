import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { FolderViewComponent } from './folder-view/folder-view.component';
import { SystemComponent } from './system/system.component';
import { RootComponent } from './root/root.component';
import { LoginComponent } from './login/login.component';
import { MediaPlayerComponent } from './media-player/media-player.component';

const routes: Routes = [
  { path: '', component: RootComponent },
  { path: 'login', component: LoginComponent },
  { path: 'folder', component: FolderViewComponent },
  { path: 'folder/', component: FolderViewComponent },
  { path: 'folder/:folderId', component: FolderViewComponent },
  { path: 'system', component: SystemComponent },
  { path: 'media-player', component: MediaPlayerComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
