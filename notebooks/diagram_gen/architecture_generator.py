import argparse
import os

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


class ArchitectureGenerator:
    def __init__(self, time_to_market: int = 12, entity=None, client_type=None, localization=None, brokerage=None,
                 transactions=None, management=None, security=('KYC', '2FA', 'AML'), cards=None, client_interface=None,
                 lendings=None, accounts=None, white_label=None):
        self.time_to_market = time_to_market
        self.entity = entity
        self.client_type = client_type
        self.localization = localization
        self.brokerage = brokerage
        self.transactions = transactions
        self.management = management
        self.security = security
        self.cards = cards
        self.client_interface = client_interface
        self.lendings = lendings
        self.accounts = accounts
        self.white_label = white_label

        # if brokerage or client_type or lendings:
        self.diagram_core_banking()
        # if transactions:
        self.diagram_transaction()
        # if management:
        self.diagram_management()
        # if security:
        self.diagram_kyc()
        self.diagram_2f()
        # if lendings:
        self.diagram_lendings()
        # if brokerage:
        self.diagram_brokerage()

    def diagram_core_banking(self):

        with Diagram("Core Banking Solution", show=False, direction="TB", filename="./src/core_banking"):
            with Cluster("Only Write DB", ):

                database_history = Database("Database History")

                if self.brokerage:
                    with Cluster("Core Banking Solution Brokerage"):
                        cbs_brokerage = [CEPH_OSD(i) for i in self.brokerage]

                        cbs_brokerage >> database_history

                if self.client_type:
                    with Cluster("Core Banking Solution Clients Data"):
                        cbs_client_data = list()

                        if self.client_type and "Private individuals" in self.client_type:
                            cbs_client_private = CEPH_OSD("clients_private")
                            cbs_client_data += [cbs_client_private]

                        if self.client_type and "Business" in self.client_type:
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

                if self.lendings:
                    with Cluster("Core Banking Solution Loans"):
                        loans = CEPH_OSD("loans")

                        database_history << loans

            with Cluster("Only Read DB"):
                replica_master = CEPH_OSD("master")
                replica_master - [CEPH_OSD("r1"),
                                  CEPH_OSD("r2"),
                                  CEPH_OSD("rn")]

        # display(diag_cbs)

    def diagram_transaction(self):

        if self.transactions:
            with Diagram("Transations", show=False, direction="TB", filename="./src/transactions"):
                with Cluster("INTERNAL"):
                    with Cluster("Core Banking Solution"):
                        cbs = CEPH_OSD("Core Banking")
                    with Cluster("Transaction Services"):
                        bth = CEPH_OSD("Backend Internal Handler")
                    with Cluster("Frontend"):
                        fe = CEPH_OSD("Frontend Interface")
                    if self.transactions and "Cryptocurrency internal" in self.transactions:
                        with Cluster("Blockain Ledger"):
                            cci = CEPH_OSD("Cryptocyrrency transactions_args Internal System")

                with Cluster("EXTERNAL"):
                    if self.transactions and "Integration 3r party solution" in self.transactions:
                        tp3 = IotBank("Transaction Provider 3rd")
                        tp3 << bth >> [cbs, fe]  # transaction 3rd
                    if self.transactions and 'Clearing house integrations' in self.transactions:
                        ch = IotBank("Clearing House")
                        cbs << bth >> ch  # clearing house integrations
                    if self.transactions and "integration 3r party solution" in self.transactions:
                        cc3 = CEPH_OSD("Cryptocyrrency transactions_args 3rd")
                        [fe, cbs] >> cc3  # crypto transactions_args 3rd
                    if self.transactions and "Cryptocurrency internal" in self.transactions:
                        ccb = CEPH_OSD("Cryptocyrrency Brockerage")
                        cbs << bth << cci >> ccb  # crypto transactions_args internal

            # display(diag_trans)

    def diagram_management(self):

        # if self.management:

            with Diagram("Orgaisation Management", show=False, direction="LR", filename="./src/management"):
                if (self.management and 'Reporting - supervision') or (
                        self.management and 'Risk Management' in self.management):
                    with Cluster("EXTERNAL"):
                        fsa = IotBank("Finanacial Supervision Authority")
                        if self.management and 'Risk Management' in self.management:
                            securities_db = CEPH_OSD("Securities public data")
                with Cluster("INTERNAL"):
                    with Cluster("Core Banking Solution"):
                        cbs = CEPH_OSD("Core Banking")

                    if self.management and 'CRM' in self.management:
                        with Cluster("All microservices in project"):
                            tho = CEPH_OSD("service")

                    with Cluster("Internal Management"):
                        if self.management and 'CRM' in self.management:
                            crm = IotBank("CRM System for internal use")
                            crm << Edge(color="firebrick", style="dashed") >> tho

                        if self.management and 'Reporting - shareholders' in self.management:
                            ir = IotBank("Internal Reporting Module (for share holders)")
                            cbs >> Edge(color="firebrick", style="dashed") >> ir  # internal reporting

                        if self.management and 'Reporting - supervision' in self.management:
                            sr = IotBank("Statutory Reporting Module (for FSA)")
                            cbs << sr >> fsa  # statutory supervision

                        if self.management and 'Branches Management' in self.management:
                            with Cluster("Internal Management"):
                                bm1 = IotBank("Branches and Local Offices Management Module")
                                bm2 = IotBank("Local Branch Access")

                                bm1 << Edge(color="firebrick",
                                            style="dashed") >> bm2  # our supervision over branches and subsidiaries
                        if self.management and 'Risk Management' in self.management:
                            with Cluster("Risk management"):
                                data_col = CEPH_OSD("data_colector")
                                data_list = [fsa, securities_db, cbs]
                                data_col << data_list

                                risk = Rack("compute risk exposition")
                                resolution = Rack("Resolution scenarios")
                                stres = Rack("Stress tests")

                                compute = [risk, resolution, stres]
                                data_col >> compute
            # display(diag_manage)

    def diagram_2f(self):

        # if self.security and "2FA" in self.security:
            with Diagram("Proces of obtaing second factor autentification or password retreiving", show=False,
                         direction="TB", filename="./src/2FA"):
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

            # display(diag_2f)

    def diagram_kyc(self):

        # if self.security and "KYC" in self.security:

            with Diagram("KYC", show=False, direction="TB", filename="./src/KYC"):

                # if "Private individuals" in client_type_args:
                with Cluster("Person Verification - mobile app only (KNY by web is prochibited!"):
                    pho = Mobile("Photo of valid document")
                    doc = Mobile("Photo of valid document")

                if self.client_type and "Business" in self.client_type:
                    with Cluster("Corporate Documents - web/mobile app"):
                        statutory = Mobile("Scans of Statutory documents")
                        representation = Mobile("Scans of representation documents")

                with Cluster("Backend"):
                    val = SiteToSiteVpng("Validation of document quality")
                    if self.client_type and "Business" in self.client_type:
                        val_corpo = SiteToSiteVpng("Validation of document quality")
                    auth_r = SiteToSiteVpng("Analysis of provider response")

                auth_s = SiteToSiteVpng("Status procesing")

                with Cluster("external KYC provider"):
                    auth_3rd = SiteToSiteVpng("external person KYC provider")
                    if self.client_type and "Business" in self.client_type:
                        corpo_registry = SiteToSiteVpng("national corporate registr")

                with Cluster("Failure"):
                    fail = Firewall("Fail")
                    fraud_f = Firewall("Frud Prevention Procedures")

                not_f = SiteToSiteVpng("Process error -> redoo")

                with Cluster("Success Veryfication"):
                    succes = IdentityAndAccessManagement("Succes")
                    succes_f = IdentityAndAccessManagement("accepting further process")

                if self.client_type and "Business" in self.client_type:
                    [statutory, representation] >> val_corpo >> corpo_registry >> auth_r

                [pho, doc] >> val >> auth_3rd >> auth_r
                auth_r >> auth_s
                auth_s >> [fail, succes]
                fail >> [fraud_f, not_f]
                succes >> succes_f

            # display(diag_kyc)

    # def diagram_lendings(lendings):
    def diagram_lendings(self):

        from diagrams import Cluster, Diagram, Edge
        from diagrams.outscale.security import IdentityAndAccessManagement, Firewall
        from diagrams.onprem.storage import CEPH_OSD
        from diagrams.generic.device import Mobile

        # # lending_options = lendings
        # lending_options = lendings

        with Diagram("Lending", show=False, direction="TB", filename="./src/lending"):

            with Cluster("Data Source"):
                with Cluster("Core Banking"):
                    failed_credits = CEPH_OSD("Credit history module")
                    peronal = CEPH_OSD("Personal creditee data")
                with Cluster("External"):
                    credit_history = CEPH_OSD("credit history database noted by financial supervision")
                    if self.lendings == "AI Scoring":
                        alternative_source = CEPH_OSD("Alternative data source")

                data_sources = CEPH_OSD("Alternative data source")
                data_sources_node = [failed_credits, peronal, credit_history]
                if self.lendings == "AI Scoring":
                    data_sources_node.append(alternative_source)

                data_sources_node >> data_sources  # merging data sources

            with Cluster("Credit Performance Module"):
                with Cluster("Static Copy of Data"):
                    test_data = CEPH_OSD("depersonalised data input")
                    output_model = CEPH_OSD("development scoring model")
                    # output_model_prod = CEPH_OSD("production scoring model")

                with Cluster("Model Computation"):
                    score_engine = CEPH_OSD(
                        "Traditional Score Engine") if self.lendings == "Traditional Scoring" else CEPH_OSD(
                        "AI Score Ingine")

                data_sources >> test_data  # compy data to independet database
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

        # display(diag_lending)

    # brokerage = ('Bonds', 'Listed shares', 'Unlisted securities', 'Derivatives', 'Listed Receivables')

    # transations = ('Clearing house integrations',)

    def diagram_brokerage(self):

        # if self.brokerage:
            with Diagram("Brokerage", show=False, direction="TB", filename="./src/brokerage"):

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
                        if self.brokerage and "Bonds" in self.brokerage:
                            bon = CEPH_OSD("Bonds")
                            bon << cbs
                            bon >> risk_management

                        if self.brokerage and "Listed shares" in self.brokerage:
                            list = CEPH_OSD("Listed shares")
                            list << cbs
                            list >> risk_management

                        if self.brokerage and "Unlisted securities" in self.brokerage:
                            uns = CEPH_OSD("Unlisted securities")
                            uns << cbs
                            uns >> risk_management

                        if self.brokerage and "Derivatives" in self.brokerage:
                            der = CEPH_OSD("Derivatives")
                            der << cbs
                            der >> risk_management

                        if self.brokerage and "Listed Receivables" in self.brokerage:
                            lrec = CEPH_OSD("Listed Receivables")
                            lrec << cbs
                            lrec >> risk_management

            # display(diag_brokerage)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fintech Architecture Generator")
    parser.add_argument("--time_to_market", help="time to market, default = 12")
    parser.add_argument("--entity", help="time to market, default = 12")
    parser.add_argument("--client_type", help="time to market, default = 12")
    parser.add_argument("--localization", help="time to market, default = 12")
    parser.add_argument("--brokerage", help="time to market, default = 12")
    parser.add_argument("--transactions", help="time to market, default = 12")
    parser.add_argument("--management", help="time to market, default = 12")
    parser.add_argument("--security", help="time to market, default = 12")
    parser.add_argument("--cards", help="time to market, default = 12")
    parser.add_argument("--client_interface", help="time to market, default = 12")
    parser.add_argument("--lendings", help="time to market, default = 12")
    parser.add_argument("--accounts", help="time to market, default = 12")
    parser.add_argument("--white_label", help="time to market, default = 12")

    os.environ.pop('SERVER_NAME', None)

    args = parser.parse_args()

    ArchitectureGenerator(vars(args))

    # display(vars(args))

    # import pprint
    #
    # pprint.pprint(vars(args))
