import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';
import { Url } from 'src/app/drive/urls';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { GetStorageProviderTypesResponse, StorageProviderType } from '../models';
import { Title } from '@angular/platform-browser';

@Component({
  selector: 'app-setup',
  templateUrl: './setup.component.html',
  styleUrls: ['./setup.component.scss']
})
export class SetupComponent implements OnInit {
  loadingLevel: number = 0;
  setupForm: FormGroup;
  storageProviderTypes: StorageProviderType [] = [];
  submissionError: string = '';
  
  constructor(private service: CommonService,
              private router: Router,
              private formBuilder: FormBuilder,
              private titleService: Title) {
                this.titleService.setTitle('Setup - RPi Drive');
              }

  ngOnInit(): void {
    // Load StorageProvider types
    this.loadingLevel++;
    this.service.getStorageProviderTypes().subscribe((response : GetStorageProviderTypesResponse) => {
      this.storageProviderTypes = response.values;
    }).add(() => {
      this.loadingLevel--;
    });

    // Check whether RPi Drive has been initialized
    this.loadingLevel++;
    this.service.isSystemInitialized().subscribe(() => {}, error => {
      this.router.navigateByUrl(Url.getFolderAbsURL());
    }).add(() => {
      this.loadingLevel--;
    });

    this.setupForm = this.formBuilder.group({
      initKey: ['', Validators.required],
      user: this.formBuilder.group({
        firstName: ['', Validators.required],
        lastName: ['', Validators. required],
        email: ['', [Validators.required, Validators.email]],
        username: ['', Validators.required],
        password: ['', Validators.required],
        passwordVerify: ['', Validators.required],
        isActive: [true],
        isSuperuser: [true],
      }),
      storageProvider: this.formBuilder.group({
        name: ['', Validators.required],
        type: ['', Validators.required],
        path: ['', Validators.required]
      })
    });
  }

  onSubmit() {
    this.loadingLevel += 1;
    this.service.initializeSystem(this.setupForm.value).subscribe(() => {
      this.router.navigateByUrl(Url.getLoginAbsURL());
    }, error => {
      this.submissionError = error.error['error'];
    }).add(() => {
      this.loadingLevel -= 1;
    })
  }
}
