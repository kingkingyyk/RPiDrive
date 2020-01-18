import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { FolderViewComponent } from './folder-view/folder-view.component';

const routes: Routes = [
  { path: 'drive/folder/:folderId', component: FolderViewComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
