import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PictureViewerComponent } from './picture-viewer.component';

describe('PictureViewerComponent', () => {
  let component: PictureViewerComponent;
  let fixture: ComponentFixture<PictureViewerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PictureViewerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PictureViewerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
