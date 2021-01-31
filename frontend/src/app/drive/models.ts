export interface GetStorageProviderTypesResponse {
    values: StorageProviderType []
}

export interface StorageProviderType {
    name: string;
    value: string;
}

export class StorageProvider {
    id: number;
    name: string;
    type: string;
    path: string;

    construct(data: any) {
        this.id = data['id'];
        this.name = data['name'];
        this.type = data['type'];
        this.path = data['path'];
    }
}

export class InitializeSystem {
    user: User;
    storage: StorageProvider;
    initKey: string;
}

export class User {
    username: string;
    password: string;
    firstName: string;
    lastName: string;
    email: string;
    isActive: boolean;
    isSuperuser: boolean;
}

export interface IsLoggedInResponse {
    result: boolean;
}

export class Login {
    username: string;
    password: string;
}