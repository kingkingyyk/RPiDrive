import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmDeletePlaylistComponent } from './confirm-delete-playlist.component';

describe('ConfirmDeletePlaylistComponent', () => {
  let component: ConfirmDeletePlaylistComponent;
  let fixture: ComponentFixture<ConfirmDeletePlaylistComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ConfirmDeletePlaylistComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfirmDeletePlaylistComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
