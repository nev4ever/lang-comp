package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"strconv"
)

type orderRequest struct {
	CustomerID int `json:"customerId"`
	ItemCount  int `json:"itemCount"`
	BaseCents  int `json:"baseCents"`
}

type orderResponse struct {
	OK         bool   `json:"ok"`
	OrderID    int    `json:"orderId"`
	TotalCents int    `json:"totalCents"`
	Error      string `json:"error,omitempty"`
}

func sqliteQuery(db string, sql string) (string, error) {
	cmd := exec.Command("sqlite3", db, sql)
	var out bytes.Buffer
	var errBuf bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &errBuf
	if err := cmd.Run(); err != nil {
		if errBuf.Len() > 0 {
			return "", fmt.Errorf("%s", errBuf.String())
		}
		return "", err
	}
	return string(bytes.TrimSpace(out.Bytes())), nil
}

func initDB(db string) error {
	_, err := sqliteQuery(db, "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, total_cents INTEGER NOT NULL);")
	return err
}

func main() {
	port := flag.Int("port", 0, "")
	db := flag.String("db", "", "")
	flag.Parse()
	if *port == 0 || *db == "" {
		fmt.Fprintln(os.Stderr, "Usage: go_pipeline --port <n> --db <path>")
		os.Exit(1)
	}
	if err := initDB(*db); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	http.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"ok":true}`))
	})

	http.HandleFunc("/orders", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "POST" {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		body, err := io.ReadAll(r.Body)
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(orderResponse{OK: false, Error: err.Error()})
			return
		}
		var req orderRequest
		if err := json.Unmarshal(body, &req); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(orderResponse{OK: false, Error: err.Error()})
			return
		}

		total := req.BaseCents*req.ItemCount + (req.CustomerID % 7)
		out, err := sqliteQuery(*db, fmt.Sprintf("BEGIN; INSERT INTO orders(customer_id,total_cents) VALUES(%d,%d); SELECT last_insert_rowid(); COMMIT;", req.CustomerID, total))
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(orderResponse{OK: false, Error: err.Error()})
			return
		}
		re := regexp.MustCompile(`\d+`)
		m := re.FindAllString(out, -1)
		orderID := 0
		if len(m) > 0 {
			orderID, _ = strconv.Atoi(m[len(m)-1])
		}
		storedRaw, err := sqliteQuery(*db, fmt.Sprintf("SELECT total_cents FROM orders WHERE id=%d;", orderID))
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			_ = json.NewEncoder(w).Encode(orderResponse{OK: false, Error: err.Error()})
			return
		}
		stored, _ := strconv.Atoi(storedRaw)
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(orderResponse{OK: true, OrderID: orderID, TotalCents: stored})
	})

	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	if err := http.ListenAndServe(addr, nil); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
