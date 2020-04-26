import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RequiresLoginComponent } from './requires-login.component';

describe('RequiresLoginComponent', () => {
  let component: RequiresLoginComponent;
  let fixture: ComponentFixture<RequiresLoginComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RequiresLoginComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RequiresLoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
