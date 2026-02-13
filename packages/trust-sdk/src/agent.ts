import { createAgent, IResolver, IDataStore, IKeyManager, IDIDManager, TAgent } from '@veramo/core'
import { CredentialPlugin, ICredentialIssuer, ICredentialVerifier } from '@veramo/credential-w3c'
import { DIDManager } from '@veramo/did-manager'
import { EthrDIDProvider } from '@veramo/did-provider-ethr'
import { KeyDIDProvider } from '@veramo/did-provider-key'
import { DIDResolverPlugin } from '@veramo/did-resolver'
import { KeyManager } from '@veramo/key-manager'
import { KeyManagementSystem, SecretBox } from '@veramo/kms-local'
import { Entities, KeyStore, DIDStore, PrivateKeyStore, IDataStoreORM, DataStore, DataStoreORM } from '@veramo/data-store'
import { Resolver } from 'did-resolver'
import { getResolver as ethrDidResolver } from 'ethr-did-resolver'
import { getResolver as keyDidResolver } from 'key-did-resolver'
import { DataSource } from 'typeorm'
import 'reflect-metadata'

export type Agent = TAgent<IDIDManager & IKeyManager & IDataStore & IDataStoreORM & IResolver & ICredentialIssuer & ICredentialVerifier>

const DATABASE_FILE = '/tmp/database.sqlite'
const SECRET_KEY = process.env.AGENT_SECRET_KEY
if (!SECRET_KEY) {
    throw new Error("AGENT_SECRET_KEY environment variable is required")
}

// Database Configuration
let dbConfig: any = {
    synchronize: true,
    logging: false,
    entities: Entities,
};

if (process.env.DB_HOST || process.env.INSTANCE_CONNECTION_NAME) {
    console.log('[Agent] Using PostgreSQL Database');
    dbConfig.type = 'postgres';
    if (process.env.INSTANCE_CONNECTION_NAME) {
        dbConfig.extra = {
            socketPath: `/cloudsql/${process.env.INSTANCE_CONNECTION_NAME}`
        };
    } else {
        dbConfig.host = process.env.DB_HOST;
        dbConfig.port = Number(process.env.DB_PORT) || 5432;
    }
    dbConfig.username = process.env.DB_USER;
    dbConfig.password = process.env.DB_PASSWORD;
    dbConfig.database = process.env.DB_NAME;
} else {
    console.log('[Agent] Using SQLite Database (Ephemeral)');
    dbConfig.type = 'sqlite';
    dbConfig.database = DATABASE_FILE;
}

const dbConnection = new DataSource(dbConfig)

const DID_NETWORK = process.env.DID_NETWORK || 'base-sepolia';
const RPC_URL = process.env.RPC_URL || 'https://sepolia.base.org';

export const agent: Agent = createAgent<IDIDManager & IKeyManager & IDataStore & IDataStoreORM & IResolver & ICredentialIssuer & ICredentialVerifier>({
    plugins: [
        new KeyManager({
            store: new KeyStore(dbConnection),
            kms: {
                local: new KeyManagementSystem(new PrivateKeyStore(dbConnection, new SecretBox(SECRET_KEY))),
            },
        }),
        new DIDManager({
            store: new DIDStore(dbConnection),
            defaultProvider: 'did:key',
            providers: {
                'did:ethr': new EthrDIDProvider({
                    defaultKms: 'local',
                    network: DID_NETWORK,
                    rpcUrl: RPC_URL,
                }),
                'did:key': new KeyDIDProvider({
                    defaultKms: 'local',
                }),
            },
        }),
        new DIDResolverPlugin({
            resolver: new Resolver({
                ...ethrDidResolver({
                    networks: [
                        { name: DID_NETWORK, rpcUrl: RPC_URL }
                    ]
                }),
                ...keyDidResolver(),
            }),
        }),
        new CredentialPlugin(),
        new DataStore(dbConnection),
        new DataStoreORM(dbConnection),
    ],
})

export const initAgent = async (): Promise<Agent> => {
    if (!dbConnection.isInitialized) {
        await dbConnection.initialize()
    }
    return agent
}
