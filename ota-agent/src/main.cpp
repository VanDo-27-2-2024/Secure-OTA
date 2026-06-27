#include <chrono>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>

#include <curl/curl.h>

static volatile std::sig_atomic_t g_running = 1;

void handle_signal(int signum) {
    if (signum == SIGINT || signum == SIGTERM) {
        g_running = 0;
    }
}

size_t write_callback(char* ptr, size_t size, size_t nmemb, void* userdata) {
    auto* response = static_cast<std::string*>(userdata);
    response->append(ptr, size * nmemb);
    return size * nmemb;
}

bool perform_healthcheck(const std::string& url, const std::string& ca_cert, const std::string& client_cert, const std::string& client_key, std::string& out_response, long& out_status) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "curl_easy_init failed\n";
        return false;
    }

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    if (url.rfind("https://", 0) == 0) {
        // TLS and mTLS configuration
        // Request all requests to use SSL/TLS
        curl_easy_setopt(curl, CURLOPT_USE_SSL, CURLUSESSL_ALL);
        // Explicitly enforce certificate and hostname verification for security audits
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 2L);
        // Path to the CA certificate used to verify the server
        curl_easy_setopt(curl, CURLOPT_CAINFO, ca_cert.c_str());
        // Path to the client certificate presented to the server for mTLS
        curl_easy_setopt(curl, CURLOPT_SSLCERT, client_cert.c_str());
        // Path to the private key for the client certificate
        curl_easy_setopt(curl, CURLOPT_SSLKEY, client_key.c_str());
    }

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        std::cerr << "Healthcheck request failed: " << curl_easy_strerror(res) << "\n";
        curl_easy_cleanup(curl);
        return false;
    }

    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &out_status);
    curl_easy_cleanup(curl);
    return true;
}

int main(int argc, char* argv[]) {
    const std::string default_url = "http://127.0.0.1:8000/health";
    std::string healthcheck_url = default_url;
    int interval_seconds = 30;
    std::string ca_cert = "/etc/ota/ca.crt";
    std::string client_cert = "/etc/ota/device.crt";
    std::string client_key = "/etc/ota/device.key";

    if (argc > 1) {
        healthcheck_url = argv[1];
    }
    if (argc > 2) {
        interval_seconds = std::atoi(argv[2]);
        if (interval_seconds <= 0) {
            interval_seconds = 30;
        }
    }
    if (argc > 3) {
        ca_cert = argv[3];
    }
    if (argc > 4) {
        client_cert = argv[4];
    }
    if (argc > 5) {
        client_key = argv[5];
    }

    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    std::cout << "OTA Agent starting.\n";
    std::cout << "Healthcheck URL: " << healthcheck_url << "\n";
    std::cout << "CA Cert: " << ca_cert << "\n";
    std::cout << "Client Cert: " << client_cert << "\n";
    std::cout << "Client Key: " << client_key << "\n";
    std::cout << "Press Ctrl+C to stop.\n";

    while (g_running) {
        std::string response;
        long status = 0;

        bool ok = perform_healthcheck(healthcheck_url, ca_cert, client_cert, client_key, response, status);
        if (ok) {
            std::cout << "[OK] HTTP " << status << " response: " << response << "\n";
        } else {
            std::cout << "[ERROR] Healthcheck failed.\n";
        }

        for (int i = 0; i < interval_seconds && g_running; ++i) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }

    std::cout << "OTA Agent stopping.\n";
    return 0;
}
