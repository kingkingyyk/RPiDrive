import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogNewPlaylistComponent } from './dialog-new-playlist.component';

describe('DialogNewPlaylistComponent', () => {
  let component: DialogNewPlaylistComponent;
  let fixture: ComponentFixture<DialogNewPlaylistComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogNewPlaylistComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogNewPlaylistComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
