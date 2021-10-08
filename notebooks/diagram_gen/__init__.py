from IPython.display import display
from diagrams import Cluster, Diagram
from diagrams import Edge
from diagrams.aws.iot import IotBank
from diagrams.generic.compute import Rack
from diagrams.generic.device import Mobile
from diagrams.onprem.storage import CEPH_OSD
from diagrams.outscale.network import SiteToSiteVpng
from diagrams.outscale.security import IdentityAndAccessManagement, Firewall
from diagrams.programming.flowchart import Database



def diagram_core_banking(brockerage=None, client_type=None, lendings=None):

    # ('Bonds', 'Listed shares', 'Unlisted securities', 'Derivatives', 'Receivables')
    brockerage_args = brockerage
    client_type_args = client_type
    lendings_args = lendings

    with Diagram("Core Banking Solution", show=False, direction="TB") as diag_cbs:
        with Cluster("Only Write DB", ):

            database_history = Database("Database History")

            if brockerage_args:
                with Cluster("Core Banking Solution Brokerage"):
                    cbs_brokerage = [CEPH_OSD(i) for i in brockerage_args]

                    cbs_brokerage >> database_history

            if client_type_args:
                with Cluster("Core Banking Solution Clients Data"):
                    cbs_client_data = list()

                    if "Private individuals" in client_type_args:
                        cbs_client_private = CEPH_OSD("clients_private")
                        cbs_client_data += [cbs_client_private]

                    if "Business" in client_type_args:
                        cbs_client_business_repr = CEPH_OSD("clients_business_representatives")
                        cbs_client_business_pers = CEPH_OSD("clients_business_company")
                        cbs_client_data += [cbs_client_business_repr, cbs_client_business_pers]

                    if cbs_client_data:
                        database_history << cbs_client_data

            with Cluster("Core Banking Solution Current Balances"):
                deposits = CEPH_OSD("deposits")
                transactions = CEPH_OSD("transactions")

                cbs_balances = [deposits, transactions]

                database_history << cbs_balances

            if lendings_args:
                with Cluster("Core Banking Solution Loans"):
                    loans = CEPH_OSD("loans")

                    database_history << loans


        with Cluster("Only Read DB"):
            replica_master = CEPH_OSD("master")
            replica_master - [CEPH_OSD("r1"),
                              CEPH_OSD("r2"),
                              CEPH_OSD("rn")]

    display(diag_cbs)


def diagram_transaction(transactions=None):

    transactions_args = transactions

    if transactions_args:
        with Diagram("Transations", show=False, direction="TB") as diag_trans:
            with Cluster("INTERNAL"):
                with Cluster("Core Banking Solution"):
                    cbs = CEPH_OSD("Core Banking")
                with Cluster("Transaction Services"):
                    bth = CEPH_OSD("Backend Internal Handler")
                with Cluster("Frontend"):
                    fe = CEPH_OSD("Frontend Interface")
                if "Cryptocurrency internal" in transactions_args:
                    with Cluster("Blockain Ledger"):
                        cci = CEPH_OSD("Cryptocyrrency transactions_args Internal System")

            with Cluster("EXTERNAL"):
                if "Integration 3r party solution" in transactions_args:
                    tp3 = IotBank("Transaction Provider 3rd")
                    tp3 << bth >> [cbs, fe]  # transaction 3rd
                if 'Clearing house integrations' in transactions_args:
                    ch = IotBank("Clearing House")
                    cbs << bth >> ch  # clearing house integrations
                if "integration 3r party solution" in transactions_args:
                    cc3 = CEPH_OSD("Cryptocyrrency transactions_args 3rd")
                    [fe, cbs] >> cc3  # crypto transactions_args 3rd
                if "Cryptocurrency internal" in transactions_args:
                    ccb = CEPH_OSD("Cryptocyrrency Brockerage")
                    cbs << bth << cci >> ccb  # crypto transactions_args internal


        display(diag_trans)

def diagram_management(management=None):

    management_arg = management

    if management_arg:

        with Diagram("Orgaisation Management", show=False, direction="LR") as diag_manage:
            if 'Reporting - supervision' or 'Risk Management' in management_arg:
                with Cluster("EXTERNAL"):
                    fsa = IotBank("Finanacial Supervision Authority")
                    if 'Risk Management' in management_arg:
                        securities_db = CEPH_OSD("Securities public data")
            with Cluster("INTERNAL"):
                with Cluster("Core Banking Solution"):
                    cbs = CEPH_OSD("Core Banking")

                if 'CRM' in management_arg:
                    with Cluster("All microservices in project"):
                        tho  = CEPH_OSD("service")

                with Cluster("Internal Management"):
                    if 'CRM' in management_arg:
                        crm = IotBank("CRM System for internal use")
                        crm << Edge(color="firebrick", style="dashed") >> tho

                    if 'Reporting - shareholders' in management_arg:
                        ir = IotBank("Internal Reporting Module (for share holders)")
                        cbs >> Edge(color="firebrick", style="dashed") >> ir  # internal reporting

                    if 'Reporting - supervision' in management_arg:
                        sr = IotBank("Statutory Reporting Module (for FSA)")
                        cbs << sr >> fsa  #statutory supervision

                    if 'Branches Management' in management_arg:
                        with Cluster("Internal Management"):
                            bm1 = IotBank("Branches and Local Offices Management Module")
                            bm2 = IotBank("Local Branch Access")

                            bm1 << Edge(color="firebrick", style="dashed") >> bm2  # our supervision over branches and subsidiaries
                    if 'Risk Management' in management_arg:
                        with Cluster("Risk management"):
                            data_col =  CEPH_OSD("data_colector")
                            data_list = [fsa, securities_db, cbs]
                            data_col << data_list

                            risk =  Rack("compute risk exposition")
                            resolution =  Rack("Resolution scenarios")
                            stres =  Rack("Stress tests")

                            compute = [risk, resolution, stres]
                            data_col >> compute
        display(diag_manage)


def diagram_2f(security=('KYC', '2FA', 'AML')):

    securit_args = security

    if "2FA" in securit_args:
        with Diagram("Proces of obtaing second factor autentification or password retreiving", show=False,
                     direction="TB") as diag_2f:
            fe = SiteToSiteVpng("Frintent Gateway")
            with Cluster("Gateway Center"):
                udib = CEPH_OSD("User initial credential")

                sms = SiteToSiteVpng("SMS Gateway")
                email = SiteToSiteVpng("e-mail Gateway")
                voice = SiteToSiteVpng("Voice Call")

            udb = CEPH_OSD("Verification of user input with database")

            with Cluster("High Risk od Fraud"):
                fraud = Firewall("Fail")
                fraud_f = Firewall("Frud Prevention Procedures")

            with Cluster("Success Veryfication"):
                succes = IdentityAndAccessManagement("Succes")
                succes_f = IdentityAndAccessManagement("accepting further process")

            fe >> udib >> [sms, email, voice] >> udb >> [fraud, succes]
            fraud >> fraud_f
            succes >> succes_f

        display(diag_2f)


def diagram_kyc(client_type=None, security=('KYC', '2FA', 'AML')):

    client_type_args = client_type
    securit_args = security

    if "KYC" in securit_args:

        with Diagram("KYC", show=False, direction="TB") as diag_kyc:

            # if "Private individuals" in client_type_args:
            with Cluster("Person Verification - mobile app only (KNY by web is prochibited!"):
                pho = Mobile("Photo of valid document")
                doc = Mobile("Photo of valid document")

            if "Business" in client_type_args:
                with Cluster("Corporate Documents - web/mobile app"):
                    statutory = Mobile("Scans of Statutory documents")
                    representation = Mobile("Scans of representation documents")

            with Cluster("Backend"):
                val = SiteToSiteVpng("Validation of document quality")
                if "Business" in client_type_args:
                    val_corpo = SiteToSiteVpng("Validation of document quality")
                auth_r = SiteToSiteVpng("Analysis of provider response")

            auth_s = SiteToSiteVpng("Status procesing")

            with Cluster("external KYC provider"):
                auth_3rd = SiteToSiteVpng("external person KYC provider")
                if "Business" in client_type_args:
                    corpo_registry = SiteToSiteVpng("national corporate registr")

            with Cluster("Failure"):
                fail = Firewall("Fail")
                fraud_f = Firewall("Frud Prevention Procedures")

            not_f = SiteToSiteVpng("Process error -> redoo")

            with Cluster("Success Veryfication"):
                succes = IdentityAndAccessManagement("Succes")
                succes_f = IdentityAndAccessManagement("accepting further process")

            if "Business" in client_type_args:
                [statutory, representation] >> val_corpo >> corpo_registry >> auth_r

            [pho, doc] >> val >> auth_3rd >> auth_r
            auth_r >> auth_s
            auth_s >> [fail, succes]
            fail >> [fraud_f, not_f]
            succes >> succes_f

        display(diag_kyc)


# def diagram_lendings(lendings):
def diagram_lendings(lendings):

    from diagrams import Cluster, Diagram, Edge
    from diagrams.outscale.security import IdentityAndAccessManagement, Firewall
    from diagrams.onprem.storage import CEPH_OSD
    from diagrams.generic.device import Mobile

    # lending_options = lendings
    lending_options = lendings

    with Diagram("Lending", show=False, direction="TB") as diag_lending:

        with Cluster("Data Source"):
                with Cluster("Core Banking"):
                    failed_credits = CEPH_OSD("Credit history module")
                    peronal = CEPH_OSD("Personal creditee data")
                with Cluster("External"):
                    credit_history = CEPH_OSD("credit history database noted by financial supervision")
                    if lending_options == "AI Scoring":
                        alternative_source = CEPH_OSD("Alternative data source")

                data_sources = CEPH_OSD("Alternative data source")
                data_sources_node = [failed_credits, peronal, credit_history]
                if lending_options == "AI Scoring":
                    data_sources_node.append(alternative_source)

                data_sources_node >> data_sources #merging data sources

        with Cluster("Credit Performance Module"):
            with Cluster("Static Copy of Data"):
                test_data = CEPH_OSD("depersonalised data input")
                output_model = CEPH_OSD("development scoring model")
                # output_model_prod = CEPH_OSD("production scoring model")

            with Cluster("Model Computation"):
                score_engine = CEPH_OSD(
                    "Traditional Score Engine") if lending_options == "Traditional Scoring" else CEPH_OSD("AI Score Ingine")

            data_sources >> test_data # compy data to independet database
            test_data >> score_engine >> output_model
            # output_model >> Edge(label="after validation") >> output_model_prod

        with Cluster("Current credit decision module"):
            client = Mobile("Client interface")
            model = CEPH_OSD("production scoring model")
            acceptance = IdentityAndAccessManagement("decision granted")
            decline = Firewall("decision declined")
            core_banking_credit = CEPH_OSD("core banking credit tables")

            output_model >> Edge(label="periodic update") >> model
            client >> Edge(label="credit inquery") >> model
            data_sources >> model
            model >> [acceptance, decline]
            acceptance >> [core_banking_credit, client]
            decline >> client

    display(diag_lending)




# brokerage = ('Bonds', 'Listed shares', 'Unlisted securities', 'Derivatives', 'Listed Receivables')


# transations = ('Clearing house integrations',)

def diagram_brokerage(brockerage=None):
    brokerage_args = brockerage

    if brokerage_args:
        with Diagram("Brokerage", show=False, direction="TB") as diag_brokerage:

            with Cluster("integrations - data source"):
                mds = CEPH_OSD("Data source manager")

                smb = CEPH_OSD("Securities monitor - Bloomberg")
                smb >> mds

                pubi = CEPH_OSD("Government bond registry")
                pubi >> mds

                corp = CEPH_OSD("Corporate bonds registry")
                corp >> mds

                fsdb = CEPH_OSD("Financial Statements etc registries")
                fsdb >> mds

            with Cluster("integrations -  processors"):
                fsdb = CEPH_OSD("custodian bank")
                scs = CEPH_OSD("securities clearing system")
                part = CEPH_OSD("brokerage counterparts")

                intm = CEPH_OSD("Processors integration manager")

                [fsdb, scs, part] >> intm

            with Cluster("INTERNAL"):
                with Cluster("Storage"):
                    cbs = CEPH_OSD("Core Banking")
                    documents = CEPH_OSD("Isser docuemnts")

                    cbs << Edge(color="brown", style="dotted") << documents

                with Cluster("Transactions"):
                    trs = CEPH_OSD("transaction settlement manager")

                    cbs << Edge(color="brown", style="dotted") << trs
                    trs >> Edge(color="brown", style="dotted") >> intm

                with Cluster("Analytics"):
                    ta = CEPH_OSD("Technical analysis module") << mds
                    fa = CEPH_OSD("Fundamental analysis module") << mds
                    risk_management = CEPH_OSD("Risk Managament")

                with Cluster("Registry"):
                    if "Bonds" in brokerage_args:
                        bon = CEPH_OSD("Bonds")
                        bon << cbs
                        bon >> risk_management

                    if "Listed shares" in brokerage_args:
                        list = CEPH_OSD("Listed shares")
                        list << cbs
                        list >> risk_management

                    if "Unlisted securities" in brokerage_args:
                        uns = CEPH_OSD("Unlisted securities")
                        uns << cbs
                        uns >> risk_management

                    if "Derivatives" in brokerage_args:
                        der = CEPH_OSD("Derivatives")
                        der << cbs
                        der >> risk_management

                    if "Listed Receivables" in brokerage_args:
                        lrec = CEPH_OSD("Listed Receivables")
                        lrec << cbs
                        lrec >> risk_management

        display(diag_brokerage)

