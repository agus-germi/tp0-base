package common

import (
	"bufio"
	"fmt"
	"net"
	"time"
	"strings"
	"os"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")


// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchSize	  int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	bets 	[]Bet
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// avisa que no hay más apuestas
func (c *Client) sendEnd() error {
	endMessage := fmt.Sprintf("END|%v\n", c.config.ID)
	if err := c.sendMessage(endMessage); err != nil {
		return fmt.Errorf("action: send_end | result: fail | client_id: %v | error: %w", c.config.ID, err)
	}
	return nil
}

// sendMessage handles secsure message sending (avoiding short-write)
func (c *Client) sendMessage(msg string) error {
    msgBytes := []byte(msg)

    header := []byte{
        byte(len(msgBytes) >> 24),
        byte(len(msgBytes) >> 16),
        byte(len(msgBytes) >> 8),
        byte(len(msgBytes)),
    }

    fullMsg := append(header, msgBytes...)
    total := len(fullMsg)
    sent := 0

    for sent < total {
        n, err := c.conn.Write(fullMsg[sent:])
        if err != nil {
            return err
        }
        sent += n
    }
    return nil
}

// recvMessage reads a message from the server until a newline character is found.
func (c *Client) recvMessage() (string, error) {
	reader := bufio.NewReader(c.conn)
	resp, err := reader.ReadString('\n')
	if err != nil {
		return "", err
	}
	return resp, nil
}


// processBatch reads a batch of bets from the scanner, serializes it,
// sends it to the server, and validates the acknowledgment response.
// It returns true if the end of file was reached, or false otherwise.
func (c *Client) processBatch(scanner *bufio.Scanner) (bool, error) {
	batch, err, eof := getBets(scanner, c.config.BatchSize)
	if eof {
		return true, nil
	}
	if err != nil {
		return false, err
	}

	message := serializeBatch(batch, c.config.ID)
	if err := c.sendMessage(message); err != nil {
		return false, fmt.Errorf("send message: %w", err)
	}

	log.Infof("action: batch_sent | result: success | cantidad: %v", len(batch))

	resp, err := c.recvMessage()
	if err != nil {
		return false, fmt.Errorf("action: receive_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
	}
	if !validateAck(resp) {
		return false, fmt.Errorf("action: ack | result: fail | client_id: %v | error: %v", c.config.ID, err)
	}
	return false, nil
}


// queda escuchando ganadores del server
func (c *Client) waitForWinners() error {
	log.Infof("action: consulta_ganadores | result: in_progress | client_id: %v", c.config.ID)
	reader := bufio.NewReader(c.conn)
	var allWinners []string

	for {
		msg, err := reader.ReadString('\n')
		if err != nil {
			log.Errorf("action: consulta_ganadores | result: fail | err: %v", err)
		}
		msg = strings.TrimSpace(msg)	
		if msg == "WINNERS_END" {break}
		if msg != "" {allWinners = append(allWinners, msg)}

	}
	log.Infof("action: consulta_ganadores | result: success | client_id: %v | cant_ganadores: %v",c.config.ID, len(allWinners))
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(sigChan chan os.Signal) {
		
	file, scanner, err := openBetFile("bets.csv")
	if err != nil {
		log.Errorf("action: open_csv | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}
	defer file.Close()

	c.createClientSocket()
	defer c.conn.Close() // me aseguro que la conexion se cierre https://go.dev/tour/flowcontrol/12
	for{
        select {
        case <-sigChan:
            log.Infof("action: exit | result: success | client_id: %v", c.config.ID)
            return
        default:
        }
		
		eof, err := c.processBatch(scanner)
		if err != nil {
			log.Errorf("action: process_batch | result: fail | client_id: %v | error: %v", c.config.ID, err)
			return
		}
		if eof {
			if err := c.sendEnd(); err != nil {
				log.Errorf("action: send_end | result: fail | client_id: %v | error: %v", c.config.ID, err)
			}
			if err := c.waitForWinners(); err != nil {
				log.Errorf("action: wait_winners | result: fail | client_id: %v | error: %v", c.config.ID, err)
			}
			return
		}

	}

	c.conn.Close()
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)

}
