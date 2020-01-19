import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { FolderViewComponent } from './folder-view/folder-view.component';
import { SystemComponent } from './system/system.component';

const routes: Routes = [
  { path: 'drive/folder', component: FolderViewComponent },
  { path: 'drive/folder/', component: FolderViewComponent },
  { path: 'drive/folder/:folderId', component: FolderViewComponent },
  { path: 'drive/system', component: SystemComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
