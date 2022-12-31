import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonService } from 'src/app/services/common.service';
import { IsLoggedInResponse } from '../models';
import { Url } from '../urls';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  loadingLevel: number = 0;
  loginForm: FormGroup;
  loginError: string = '';
  nextUrl: string = null;

  constructor(private service: CommonService,
              private route: ActivatedRoute,
              private router: Router,
              private formBuilder: FormBuilder,
              private titleService: Title) {
                this.titleService.setTitle('Login - RPi Drive');
              }

  ngOnInit(): void {
    this.loginForm = this.formBuilder.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    })

    this.route.queryParams.subscribe(params => {
      this.nextUrl = params['next'];
    });

    this.loadingLevel += 1;
    this.service.isLoggedIn().subscribe((data : IsLoggedInResponse) => {
      this.router.navigateByUrl(this.nextUrl || Url.getRootURL());
    }).add(() => {
      this.loadingLevel -= 1;
    })
  }

  onSubmit() {
    this.loginError = '';
    this.loadingLevel += 1;
    this.service.login(this.loginForm.value).subscribe((data : IsLoggedInResponse) => {
      this.router.navigateByUrl(this.nextUrl || Url.getRootURL());
    }, error => {
      this.loginError = error.error['error']
    }).add(() => {
      this.loadingLevel -= 1;
    })
  }

}
