import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DialogAddMediaComponent } from './dialog-add-media.component';

describe('DialogAddMediaComponent', () => {
  let component: DialogAddMediaComponent;
  let fixture: ComponentFixture<DialogAddMediaComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DialogAddMediaComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DialogAddMediaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
