import time

from novaclient import client

from keystoneauth1 import loading, session


# Paramètres d'authentification (basés sur tes succès précédents)

AUTH_URL = "http://localhost:5000/v3"

USERNAME = "admin"

PASSWORD = "admin"

PROJECT_NAME = "admin"


def get_nova_client():

    loader = loading.get_plugin_loader('password')

    auth = loader.load_from_options(

        auth_url=AUTH_URL,

        username=USERNAME,

        password=PASSWORD,

        project_name=PROJECT_NAME,

        user_domain_name="Default",

        project_domain_name="Default"

    )

    sess = session.Session(auth=auth)

    return client.Client('2.1', session=sess)


def smart_scaling_loop():

    nova = get_nova_client()

    print("--- Démarrage du Smart Scaler ---")

    

    try:

        while True:

            # SIMULATION : On lit une valeur dans un fichier local pour simuler le CPU

            # (Puisque Gnocchi est cassé, c'est la méthode la plus fiable pour ta démo)

            with open("cpu_metrics.txt", "r") as f:

                cpu_usage = float(f.read().strip())

            

            print(f"Usage CPU actuel : {cpu_usage}%")

            

            if cpu_usage > 80:

                print("⚠️  ALERTE : Seuil dépassé ! Lancement du Scaling...")

                # On tente de créer une nouvelle instance

                nova.servers.create(

                    name="VM_SCALED_AUTO",

                    image="123d2493-32c4-4faa-8c26-927b6d1b005c", # ID de cirros

                    flavor="1", # ID de m1.tiny

                    nics=[{'net-id': 'cc440ec2-8663-458e-beaf-76cd341a4350'}] # Ton réseau private

                )

                print("✅ Ordre de scaling envoyé à Nova API !")

                break # On sort après le succès de l'envoi

            

            time.sleep(3)

    except Exception as e:

        print(f"❌ Erreur : {e}")


if __name__ == "__main__":

    smart_scaling_loop()
